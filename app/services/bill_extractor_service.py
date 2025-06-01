from pdf2image import convert_from_path
import pytesseract
from collections import Counter
import re
import spacy
from ..schemas.receipt_file import ReceiptFile
from ..schemas.receipt import Receipt
from sqlalchemy.orm import Session
from ..config.db import engine
from fastapi import UploadFile
import os
import uuid
from ..config.config import UPLOAD_DIR
from ..utils.pdf_validator import validate_pdf_file
from dateutil import parser
from fastapi import HTTPException




class BillExtractorService:
    def __init__(self, db):
        self.nlp = spacy.load("en_core_web_sm")
        self.db = db
        
                
    def first_letter_capitalized(self, word):
        return len(word) > 0 and word[0].isupper()
    
    def score_brand_names(self, text):
        lower_score_stopwords = {"for", "total", "with", "you", "your", "if", "enter", "password", "bill", "receipt", "please", "are", "the"}
        
        # Preprocess text
        words = re.findall(r'\b[\w.-]+\b', text)  # Extract words without punctuation
        price_pattern = re.compile(r'\$\d+(\.\d+)?|\b\d+\.\d{2}\b')
        prices = price_pattern.findall(text)

        word_scores = Counter()
        word_counts = Counter(words)
        print(words)
        
        for i, word in enumerate(words):
            lenword = len(word)
            if lenword < 3: 
                continue
            if word.lower() in lower_score_stopwords:
                continue
            score = 0
            score_boost = 1
            
            if i < 10: 
                score_boost *= (10 - i) /2 
            
            if i >= 2 and i + 2 < len(words): # We will check if 2 words before current word and 2 words after current words are capitalized or not, this heps because usually if they are not then most probably current word is a brand name.
                if (self.first_letter_capitalized(words[i]) and 
                (not self.first_letter_capitalized(words[i - 1])) and 
                (not self.first_letter_capitalized(words[i + 1]))):
                    score_boost = 1.5

            if any(domain in word.lower() for domain in [".com", ".org", ".in"]):
                score_boost *= 10
            
                
            for price in prices:
                if price in text[max(0, text.find(word) - 20): text.find(word) + 20]:  # Look within a 20-character window
                    score_boost *= 0.9
            
            if not word.isdigit() and lenword > 2:
                score += word_counts[word]
                score += score_boost * 1  # we give extra score if lenght is more than 3 as most brand might have

            
            if word == "CHARGE":
                print(f"So far score for charge {score} /// {score_boost}")
            # Check for bigrams and trigrams where all words have capital first letters
            if i + 1 < len(words) and words[i][0].isupper() and words[i + 1][0].isupper():
                bigram = f"{words[i]} {words[i + 1]}"
                word_scores[bigram] += score_boost * (1.5 * word_counts[words[i]])  # scale the score by the count of words by 1.5
            
            if i + 2 < len(words) and words[i][0].isupper() and words[i + 1][0].isupper() and words[i + 2][0].isupper():
                trigram = f"{words[i]} {words[i + 1]} {words[i + 2]}"
                word_scores[trigram] += score_boost * (2 * word_counts[words[i]])  # scale the score by the count of words by 2 as trigram have higher chance
            
            word_scores[word] += score

        sorted_scores = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_scores[:7]  # Return top 7 words

    def extract_merchant_name(self, lines, brand_names, word_scores):

        score_dict = {}
        for word, score in word_scores:
            word_lower = word.lower()
            
            # If a word appears more than once in word_scores,
            # keep the highest score for it.
            if word_lower in score_dict:
                if score > score_dict[word_lower]:
                    score_dict[word_lower] = score
            else:
                score_dict[word_lower] = score
            
            for brand in brand_names:
                brand_lower = brand.lower()
                if brand_lower in word_lower:
                    if brand_lower in score_dict:
                        if score > score_dict[brand_lower]:
                            score_dict[brand_lower] = score
                    else:
                        score_dict[brand_lower] = score

        best_candidate = None
        best_score = -1
        print(score_dict)
        for candidate in brand_names:
            candidate_lower = candidate.lower()
            candidate_score = score_dict.get(candidate_lower, 0)
            
            # Check if any line exactly equals the candidate; if yes, add a bonus.
            for line in lines:
                if line.strip().lower() == candidate_lower:
                    candidate_score += 2  # bonus: candidate exactly matches a full line
            
            # candidate with highest score.
            if candidate_score > best_score:
                best_score = candidate_score
                best_candidate = candidate

        # if no candidate was found in word_scores, we take first candidate from brand_names.
        if best_candidate is None and brand_names:
            best_candidate = brand_names[0]

        return best_candidate

    def extract_brand_names(self, ocr_text, header_lines=50, footer_lines=30):
        lines = ocr_text.strip().split('\n')
        if len(lines) > header_lines + footer_lines:
            relevant_lines = "\n".join(lines[:header_lines] + lines[-footer_lines:]) # Most probably between the bill there will be just items, we don't need that 
        else:
            relevant_lines = "\n".join(lines)
        doc = self.nlp(relevant_lines)
        brand_names = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
        return brand_names


    async def upload_pdf(self, file:UploadFile):
        _, file_extension = os.path.splitext(file.filename)
        unique_base_name = f"{uuid.uuid4()}{file_extension.lower()}"
        file_path = os.path.join(UPLOAD_DIR, unique_base_name)
        try:
            with open(file_path, "wb") as buffer:
                while contents := await file.read(1024 * 1024):
                    buffer.write(contents)
            print(f"File '{file.filename}' saved to: {file_path}")
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise IOError(f"Failed to save file '{file.filename}': {e}") from e
        
        session = Session(bind=engine)
        new_receipt = ReceiptFile(
            file_name=file.filename,
            file_path=file_path,
            is_valid=True,
            invalid_reason=None,
            is_processed=False
        )
        session.add(new_receipt)
        session.commit()
        session.refresh(new_receipt)
        return new_receipt
    
    async def validate(self, receipt_file_id:int):
        db_receipt_file = self.db.query(ReceiptFile).filter(ReceiptFile.id == receipt_file_id).first()
        is_valid, invalid_reason = validate_pdf_file(db_receipt_file.file_path)
        db_receipt_file.is_valid = is_valid
        db_receipt_file.invalid_reason = invalid_reason
        self.db.add(db_receipt_file)
        self.db.commit()
        self.db.refresh(db_receipt_file)
        return db_receipt_file

    def extract_datetime(self, text):
        # Regex to find likely date/time substrings
        datetime_patterns = r'''
            (?<!\d)(                             
                (?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}   # e.g., 08/27/2023
                \s+                               # space between date and time
                \d{1,2}:\d{2}                     # e.g., 5:35
                (?:\s*[APap][Mm])?)               # optional AM/PM
            |
                (?:\d{1,2}:\d{2}\s*[APap][Mm])    # e.g., 5:35 PM
            |
                (?:\d{4}[/-]\d{1,2}[/-]\d{1,2}    # e.g., 2023-08-27
                \s+\d{1,2}:\d{2}(?::\d{2})?       # time part with optional seconds
                (?:\s*[APap][Mm])?)               # optional AM/PM
            )
        '''
        
        regex = re.compile(datetime_patterns, re.IGNORECASE | re.VERBOSE)
        candidates = regex.findall(text)

        parsed_datetimes = []
        for candidate in candidates:
            try:
                dt = parser.parse(candidate, fuzzy=True)
                parsed_datetimes.append(dt)
            except:
                continue
        return parsed_datetimes



    
    def process(self, receipt_file_id:int):
        db_receipt_file = self.db.query(ReceiptFile).filter(ReceiptFile.id == receipt_file_id).first()
        if not db_receipt_file: 
            raise HTTPException(status_code=404, detail="Receipt file not found")
        if not db_receipt_file.is_valid:
            raise HTTPException(status_code=400, detail="Receipt file either not valid or not validated yet")
        
        images = convert_from_path(db_receipt_file.file_path, dpi=300)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)
        rawlines = text.splitlines()
        lines = [line for line in rawlines if line.strip()]

        brand_names = self.extract_brand_names(ocr_text=text)
        word_scores = self.score_brand_names(text)
        merchant_name = self.extract_merchant_name(lines, brand_names, word_scores)
        
        purchased_at = self.extract_datetime(text)

        # Find total
        total_keywords = ['total', 'amount', 'grand total']
        total_amount = None
        for line in reversed(lines):
            for keyword in total_keywords:
                if keyword in line.lower():
                    match = re.search(r'(\d+\.\d{2})', line)
                    if match:
                        total_amount = match.group()
                        break
            if total_amount:
                break
            
        print(f"Merchant::: {merchant_name}")
        print(f"purchase at ::: ")
        print(purchased_at)
        print(f"total ::: {total_amount}")
        session = Session(bind=engine)
        new_receipt = Receipt(
            merchant_name=merchant_name,
            purchased_at=purchased_at[0] if len(purchased_at) > 0 else None,
            total_amount=total_amount,
            file_path=db_receipt_file.file_path,
        )
        session.add(new_receipt)
        session.commit()
        session.refresh(new_receipt)
        return new_receipt
    
    def getReceipt(self, id:int):
        db_receipt = self.db.query(Receipt).filter(Receipt.id == id).first()
        print(db_receipt.purchased_at)
        return db_receipt
    
    def receipts(self):
        db_receipts = self.db.query(Receipt).all()
        return db_receipts