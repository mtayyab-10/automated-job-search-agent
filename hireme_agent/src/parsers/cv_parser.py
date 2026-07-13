import json
import re
from google import genai
from src.config import settings
from src.parsers.cv_extractor import extract_text
from src.memory import cv_store

def fallback_parse_cv(raw_text: str) -> dict:
    """
    Fallback regex-based CV parser when OpenAI API is unavailable.
    Extracts basic info using pattern matching.
    """
    parsed_data = {
        "name": "Unknown Candidate",
        "email": "",
        "phone": "",
        "location": "",
        "summary": raw_text[:200],
        "skills": [],
        "experience": [],
        "education": [],
        "preferred_roles": [],
        "preferred_industries": []
    }
    
    # Try to extract email
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', raw_text)
    if email_match:
        parsed_data["email"] = email_match.group()
    
    # Try to extract phone
    phone_match = re.search(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b', raw_text)
    if phone_match:
        parsed_data["phone"] = phone_match.group()
    
    # Extract skills section if it exists
    skills_match = re.search(r'skills?:?\s*\n((?:[^\n]*\n?)*?)(?=\n(?:experience|education|$))', raw_text, re.IGNORECASE)
    if skills_match:
        skills_text = skills_match.group(1)
        parsed_data["skills"] = [s.strip() for s in skills_text.split(',') if s.strip()]
    
    print("Using fallback CV parser (Gemini API unavailable)")
    return parsed_data

def parse_cv_text(raw_text: str) -> dict:
    """
    Sends the raw text to Gemini to parse into a specific JSON structure.
    Falls back to regex-based parsing if Gemini API fails.
    """
    try:
        if not getattr(settings, "GEMINI_API_KEY", None):
            return fallback_parse_cv(raw_text)

        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        system_prompt = (
            "You are an expert CV parser. Extract information from the provided CV text. "
            "You must return ONLY a raw JSON object. Do not include markdown block formatting, "
            "no explanation, no markdown text, and no code fences (do not wrap in ```json or ```).\n\n"
            "The JSON structure must be:\n"
            "{\n"
            '  "name": "string",\n'
            '  "email": "string",\n'
            '  "phone": "string",\n'
            '  "location": "string",\n'
            '  "summary": "string",\n'
            '  "skills": ["string", ...],\n'
            '  "experience": [\n'
            "    {\n"
            '      "title": "string",\n'
            '      "company": "string",\n'
            '      "duration": "string",\n'
            '      "description": "string"\n'
            "    }, ...\n"
            "  ],\n"
            '  "education": [\n'
            "    {\n"
            '      "degree": "string",\n'
            '      "institution": "string",\n'
            '      "year": "string"\n'
            "    }, ...\n"
            "  ],\n"
            '  "preferred_roles": ["string", ...],\n'
            '  "preferred_industries": ["string", ...]\n'
            "}"
        )

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"{system_prompt}\n\nCV TEXT:\n{raw_text}",
        )

        raw_response = (response.text or "").strip()
        if not raw_response:
            raise ValueError("Gemini returned an empty response")

        # Clean any accidental markdown fence output
        cleaned_response = raw_response
        if cleaned_response.startswith("```"):
            cleaned_response = re.sub(r"^```[a-zA-Z]*\n", "", cleaned_response)
            cleaned_response = re.sub(r"\n```$", "", cleaned_response)
            cleaned_response = cleaned_response.strip()

        try:
            parsed_data = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse Gemini JSON response: {e}\nRaw Response:\n{raw_response}"
            ) from e

        candidate_name = parsed_data.get("name", "Unknown")
        print(f"Successfully parsed CV for candidate: {candidate_name}")
        return parsed_data
    
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            print(f"Gemini API quota exceeded or rate limited: {e}")
        else:
            print(f"Gemini API error: {e}")
        
        # Use fallback parser
        return fallback_parse_cv(raw_text)

def ingest_cv(uploaded_file) -> dict:
    """
    Extracts text, parses it, saves the results to the memory cv_store,
    and returns the final parsed dict.
    """
    raw_text = extract_text(uploaded_file)
    parsed_cv = parse_cv_text(raw_text)
    cv_store.save_cv(parsed_cv)
    return parsed_cv
