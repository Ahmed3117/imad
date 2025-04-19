#^ < ==============================[ <- Ai models -> ]============================== > ^#


import os
import tempfile
import json
import re
import traceback
import fitz  # PyMuPDF
import requests
import google.generativeai as genai
import google.api_core.exceptions
from PIL import Image
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser


class MCQGeneratorView(APIView):
    """API View to generate MCQs from uploaded PDF files using Gemini or OpenRouter models."""
    parser_classes = (MultiPartParser, FormParser)

    # Configuration constants
    DEFAULT_GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "")
    DEFAULT_OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', "")
    DEFAULT_OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    
    # Available models and languages
    AVAILABLE_MODELS = {
        "gemini-flash": "gemini-1.5-flash-latest",  
        "gemini-flash-2": "gemini-2.0-flash",            
        "gemini-pro": "gemini-1.5-pro",            
        "deepseek": "deepseek/deepseek-r1:free"     
    }
    SUPPORTED_LANGUAGES = ["en", "ar"]
    
    # Maximum text length for models
    MAX_CHARS_GEMINI = 25000
    MAX_CHARS_OPENROUTER = 20000

    def post(self, request, *args, **kwargs):
        """Handle POST requests to generate MCQs from PDF files."""
        # Validate input file
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if not file.name.lower().endswith('.pdf'):
            return Response({"error": "Only PDF files are supported"}, status=status.HTTP_400_BAD_REQUEST)

        # Extract and validate parameters
        try:
            num_questions = int(request.data.get('num_questions', 5))
            if num_questions <= 0:
                return Response({"error": "Number of questions must be positive."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid number of questions provided."}, status=status.HTTP_400_BAD_REQUEST)

        model_option = request.data.get('model', 'gemini-flash').lower()
        language = request.data.get('lang', 'en').lower()

        if model_option not in self.AVAILABLE_MODELS:
            return Response(
                {"error": f"Invalid model option. Available options: {', '.join(self.AVAILABLE_MODELS.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if language not in self.SUPPORTED_LANGUAGES:
            return Response(
                {"error": f"Invalid language. Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_name = self.AVAILABLE_MODELS[model_option]

        # Process file and generate MCQs
        temp_path = None
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp:
                for chunk in file.chunks():
                    temp.write(chunk)
                temp_path = temp.name

            # Extract text from PDF
            pdf_text = self.extract_text_from_pdf(temp_path)
            if not pdf_text or pdf_text.strip() == "":
                return Response({"error": "Failed to extract text from PDF or PDF is empty."}, 
                               status=status.HTTP_400_BAD_REQUEST)

            # Generate MCQs based on selected model
            print(f"Generating MCQs using model: {model_option}, language: {language}")
            
            if model_option.startswith('gemini'):
                mcqs = self.generate_mcqs_with_gemini(pdf_text, model_name, num_questions, language)
            else:
                mcqs = self.generate_mcqs_with_openrouter(pdf_text, model_name, num_questions, language)

            # Validate generation results
            if not mcqs or not isinstance(mcqs, list) or (len(mcqs) == 0 and num_questions > 0):
                return Response({"error": "Failed to generate MCQs. Check server logs for details."}, 
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return success response
            return Response({
                "message": f"Successfully generated {len(mcqs)} MCQs in {language.upper()}",
                "num_questions_generated": len(mcqs),
                "num_questions_requested": num_questions,
                "language": language,
                "model_used": model_name,
                "mcqs": mcqs
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in POST request: {e}")
            print(traceback.format_exc())
            return Response({"error": f"An unexpected server error occurred: {e}"}, 
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error cleaning up temporary file {temp_path}: {e}")

    def extract_text_from_pdf(self, pdf_path):
        """Extract text content from a PDF file using PyMuPDF."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text("text", sort=True)
                if page_text:
                    text += page_text.strip() + "\n\n"
            doc.close()
            return text.strip()
        except Exception as e:
            print(f"Error reading PDF '{pdf_path}': {e}")
            print(traceback.format_exc())
            return None

    def clean_json_response(self, raw_text):
        """Extract JSON from model output text."""
        if not raw_text:
            return None

        # Try finding JSON within markdown code blocks
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            potential_json = match.group(1).strip()
            if (potential_json.startswith('[') and potential_json.endswith(']')) or \
               (potential_json.startswith('{') and potential_json.endswith('}')):
                return potential_json

        # Try finding JSON by brackets
        start_bracket = raw_text.find('[')
        start_curly = raw_text.find('{')

        if start_bracket == -1 and start_curly == -1:
            return None

        # Determine start and end
        if start_bracket != -1 and (start_curly == -1 or start_bracket < start_curly):
            start_index = start_bracket
            end_char = ']'
        else:
            start_index = start_curly
            end_char = '}'

        end_index = raw_text.rfind(end_char)
        if end_index == -1 or end_index < start_index:
            # Try alternate end character
            other_end_char = ']' if end_char == '}' else '}'
            other_end_index = raw_text.rfind(other_end_char)
            if other_end_index > start_index:
                end_index = other_end_index
            else:
                return None

        return raw_text[start_index:end_index + 1].strip()

    def generate_mcqs_with_gemini(self, text_content, model_name, num_questions=5, language='en'):
        """Generate MCQs using Google Gemini API."""
        print(f"Starting Gemini MCQ generation with model: {model_name}")
        
        # Get API key
        api_key = os.environ.get('GEMINI_API_KEY', self.DEFAULT_GEMINI_API_KEY)
        if not api_key:
            print("ERROR: Missing Gemini API key")
            return None

        try:
            # Configure API and create model
            genai.configure(api_key=api_key)
            
            # List available models for debugging
            available_models = [m.name.split('/')[-1] for m in genai.list_models() 
                              if 'generateContent' in m.supported_generation_methods]
            print(f"Available Gemini models: {available_models}")
            
            # Create model instance
            model = genai.GenerativeModel(model_name)
            print(f"Created model instance: {model.model_name}")
            
            # Truncate text if needed
            truncated_text = text_content[:self.MAX_CHARS_GEMINI] if len(text_content) > self.MAX_CHARS_GEMINI else text_content
            
            # Language instructions
            lang_instructions = {
                "en": "Generate the questions, options, and correct answer indications strictly in English.",
                "ar": "Generate the questions, options, and correct answer indications strictly in Arabic."
            }
            
            # Create prompt
            prompt = self._create_mcq_prompt(truncated_text, num_questions, lang_instructions.get(language, lang_instructions["en"]), language)
            
            # Generation config
            generation_config = genai.types.GenerationConfig(temperature=1)
            
            # Generate content
            print("Sending request to Gemini...")
            response = model.generate_content(prompt, generation_config=generation_config)
            
            # Process response
            if not response.candidates:
                print("ERROR: Gemini response blocked or empty")
                return None
                
            raw_text = response.text
            print(f"Received response (preview): {raw_text[:200]}...")
            
            # Parse JSON
            cleaned_json = self.clean_json_response(raw_text)
            if cleaned_json:
                try:
                    mcqs = json.loads(cleaned_json)
                    if isinstance(mcqs, list):
                        print(f"Successfully parsed JSON with {len(mcqs)} items")
                        return mcqs
                    elif isinstance(mcqs, dict):
                        print("Found single MCQ object, wrapping in list")
                        return [mcqs]
                    else:
                        print(f"ERROR: Unexpected JSON structure: {type(mcqs)}")
                        return None
                except json.JSONDecodeError as e:
                    print(f"ERROR: JSON decode failed: {e}")
                    return None
            else:
                print("ERROR: Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"ERROR in Gemini MCQ generation: {e}")
            print(traceback.format_exc())
            return None

    def generate_mcqs_with_openrouter(self, text_content, model_name, num_questions=5, language='en'):
        """Generate MCQs using OpenRouter API."""
        print(f"Starting OpenRouter MCQ generation with model: {model_name}")
        
        # Get API key
        api_key = os.environ.get('OPENROUTER_API_KEY', self.DEFAULT_OPENROUTER_API_KEY)
        if not api_key:
            print("ERROR: Missing OpenRouter API key")
            return None
            
        try:
            # Truncate text if needed
            truncated_text = text_content[:self.MAX_CHARS_OPENROUTER] if len(text_content) > self.MAX_CHARS_OPENROUTER else text_content
            
            # Language instructions
            lang_instructions = {
                "en": "Generate the questions, options, and correct answer indications strictly in English.",
                "ar": "Generate the questions, options, and correct answer indications strictly in Arabic."
            }
            
            # Create prompt
            prompt = self._create_mcq_prompt(truncated_text, num_questions, lang_instructions.get(language, lang_instructions["en"]), language)
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "MCQ-Generator",
                "X-Title": "PDF MCQ Generator"
            }
            
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 1
            }
            
            # Send request
            print(f"Sending request to OpenRouter...")
            response = requests.post(
                self.DEFAULT_OPENROUTER_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=180
            )
            
            print(f"OpenRouter response status: {response.status_code}")
            if response.status_code != 200:
                print(f"ERROR: OpenRouter returned status {response.status_code}")
                return None
                
            # Process response
            response_data = response.json()
            if 'choices' not in response_data or not response_data['choices']:
                print("ERROR: Invalid response structure")
                return None
                
            content = response_data['choices'][0]['message']['content']
            print(f"Received response (preview): {content[:200]}...")
            
            # Parse JSON
            cleaned_json = self.clean_json_response(content)
            if cleaned_json:
                try:
                    mcqs = json.loads(cleaned_json)
                    if isinstance(mcqs, list):
                        print(f"Successfully parsed JSON with {len(mcqs)} items")
                        return mcqs
                    else:
                        print(f"ERROR: Unexpected JSON structure: {type(mcqs)}")
                        return None
                except json.JSONDecodeError as e:
                    print(f"ERROR: JSON decode failed: {e}")
                    return None
            else:
                print("ERROR: Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"ERROR in OpenRouter MCQ generation: {e}")
            print(traceback.format_exc())
            return None

    def _create_mcq_prompt(self, text_content, num_questions, lang_instruction, language):
        """Create a standardized prompt for MCQ generation."""
        return f"""
        Context Text:
        --- START OF TEXT ---
        {text_content}
        --- END OF TEXT ---

        Task:
        Based *only* on the key information within the provided "Context Text", generate exactly {num_questions} multiple-choice questions (MCQs).

        Instructions:
        1.  Each MCQ must test comprehension of the provided text. Do not use external knowledge.
        2.  For each MCQ, provide:
            a.  A clear question relevant to the text.
            b.  Four distinct options labeled "A", "B", "C", "D". One option must be the correct answer based *solely* on the text. The other three must be plausible but incorrect distractors based on the text or closely related concepts.
            c.  The single capital letter (A, B, C, or D) corresponding to the correct answer.
        3.  Language: {lang_instruction}
        4.  Output Format: Respond ONLY with a valid JSON list (array) of objects. Do NOT include any text before the opening bracket `[` or after the closing bracket `]`. Do not use markdown formatting like ```json.
        5.  JSON Structure: Each object in the list must strictly follow this structure:
            {{
                "question": "The question text in {language.upper()}",
                "options": {{
                    "A": "Option A text in {language.upper()}",
                    "B": "Option B text in {language.upper()}",
                    "C": "Option C text in {language.upper()}",
                    "D": "Option D text in {language.upper()}"
                }},
                "correct_answer": "LETTER"
            }}
            - Replace "LETTER" with the single capital letter (A, B, C, or D) of the correct option.
            - Ensure keys are exactly "question", "options", "correct_answer".
            - The value for "options" must be a JSON object (dictionary).

        Generate exactly {num_questions} MCQs now in the specified JSON format.
        """



class ImageMCQExtractorView(APIView):
    """API View to extract MCQs from uploaded image files directly using AI models."""
    parser_classes = (MultiPartParser, FormParser)

    # Configuration constants
    DEFAULT_GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "")
    DEFAULT_OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', "")
    DEFAULT_OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    
    # Available models and languages
    AVAILABLE_MODELS = {
        "gemini-flash": "gemini-1.5-flash-latest",  # Supports multimodal
        "gemini-flash-2": "gemini-2.0-flash",       # Supports multimodal
        "gemini-pro": "gemini-1.5-pro",             # Supports multimodal
        "deepseek": "deepseek/deepseek-r1:free"     # Text-only fallback
    }
    SUPPORTED_LANGUAGES = ["en", "ar"]
    
    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def post(self, request, *args, **kwargs):
        """Handle POST requests to extract MCQs from image files."""
        # Validate input file
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if file.size > self.MAX_FILE_SIZE:
            return Response({"error": f"File too large. Maximum size is {self.MAX_FILE_SIZE/1024/1024}MB"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        file_extension = os.path.splitext(file.name.lower())[1]
        if file_extension not in self.SUPPORTED_IMAGE_FORMATS:
            return Response(
                {"error": f"Unsupported file format. Supported formats: {', '.join(self.SUPPORTED_IMAGE_FORMATS)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract and validate parameters
        try:
            num_questions = int(request.data.get('num_questions', 5))
            if num_questions <= 0:
                return Response({"error": "Number of questions must be positive."}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid number of questions provided."}, status=status.HTTP_400_BAD_REQUEST)

        model_option = request.data.get('model', 'gemini-flash').lower()
        language = request.data.get('lang', 'en').lower()

        if model_option not in self.AVAILABLE_MODELS:
            return Response(
                {"error": f"Invalid model option. Available options: {', '.join(self.AVAILABLE_MODELS.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if language not in self.SUPPORTED_LANGUAGES:
            return Response(
                {"error": f"Invalid language. Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_name = self.AVAILABLE_MODELS[model_option]

        # Process file and extract MCQs
        temp_path = None
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp:
                for chunk in file.chunks():
                    temp.write(chunk)
                temp_path = temp.name

            # Extract MCQs directly from image
            print(f"Processing image using model: {model_option}, language: {language}")
            
            if model_option.startswith('gemini'):
                # Gemini supports direct image input
                mcqs = self.extract_mcqs_with_gemini(temp_path, model_name, num_questions, language)
            else:
                # For other models that don't support image input, we need to use a text extraction fallback
                # This is a simplified approach - in production you might want to use a cloud OCR service
                return Response(
                    {"error": "Selected model does not support direct image processing. Please use a Gemini model."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate processing results
            if not mcqs or not isinstance(mcqs, list) or (len(mcqs) == 0 and num_questions > 0):
                return Response({"error": "Failed to extract MCQs from image. Check server logs for details."},
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return success response
            return Response({
                "message": f"Successfully extracted {len(mcqs)} MCQs in {language.upper()} from image",
                "num_questions_extracted": len(mcqs),
                "num_questions_requested": num_questions,
                "language": language,
                "model_used": model_name,
                "mcqs": mcqs
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in POST request: {e}")
            print(traceback.format_exc())
            return Response({"error": f"An unexpected server error occurred: {e}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error cleaning up temporary file {temp_path}: {e}")

    def clean_json_response(self, raw_text):
        """Extract JSON from model output text."""
        if not raw_text:
            return None

        # Try finding JSON within markdown code blocks
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            potential_json = match.group(1).strip()
            if (potential_json.startswith('[') and potential_json.endswith(']')) or \
               (potential_json.startswith('{') and potential_json.endswith('}')):
                return potential_json

        # Try finding JSON by brackets
        start_bracket = raw_text.find('[')
        start_curly = raw_text.find('{')

        if start_bracket == -1 and start_curly == -1:
            return None

        # Determine start and end
        if start_bracket != -1 and (start_curly == -1 or start_bracket < start_curly):
            start_index = start_bracket
            end_char = ']'
        else:
            start_index = start_curly
            end_char = '}'

        end_index = raw_text.rfind(end_char)
        if end_index == -1 or end_index < start_index:
            # Try alternate end character
            other_end_char = ']' if end_char == '}' else '}'
            other_end_index = raw_text.rfind(other_end_char)
            if other_end_index > start_index:
                end_index = other_end_index
            else:
                return None

        return raw_text[start_index:end_index + 1].strip()

    def extract_mcqs_with_gemini(self, image_path, model_name, num_questions=5, language='en'):
        """Extract MCQs directly from an image using Google Gemini API."""
        print(f"Starting Gemini image MCQ extraction with model: {model_name}")
        
        # Get API key
        api_key = os.environ.get('GEMINI_API_KEY', self.DEFAULT_GEMINI_API_KEY)
        if not api_key:
            print("ERROR: Missing Gemini API key")
            return None

        try:
            # Configure API
            genai.configure(api_key=api_key)
            
            # Create model instance with vision capability
            model = genai.GenerativeModel(model_name)
            print(f"Created model instance: {model.model_name}")
            
            # Language instructions
            lang_instructions = {
                "en": "Format the extracted questions, options, and correct answer indications in English.",
                "ar": "Format the extracted questions, options, and correct answer indications in Arabic."
            }
            
            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Create multimodal prompt with image and text instructions
            image_parts = [
                {
                    "mime_type": f"image/{os.path.splitext(image_path)[1][1:]}",
                    "data": base64.b64encode(image_data).decode("utf-8")
                }
            ]
            
            text_prompt = f"""
            Look at this image that contains multiple-choice questions (MCQs).

            Task:
            Analyze the image to identify the MCQs. Extract and format up to {num_questions} MCQs found in the image.

            Instructions:
            1.  Identify questions with their options (typically labeled A, B, C, D or 1, 2, 3, 4).
            2.  For each identified MCQ:
                a.  Extract the question text.
                b.  Extract all options (typically 4 options).
                c.  Identify which option is marked as correct, if indicated.
                d.  If the correct answer isn't clearly marked, make your best determination based on context.
            3.  Language: {lang_instructions.get(language, lang_instructions["en"])}
            4.  Format the JSON response using the same case (uppercase/lowercase) as seen in the image.
            5.  Output Format: Respond ONLY with a valid JSON list (array) of objects. Do NOT include any text before the opening bracket `[` or after the closing bracket `]`. Do not use markdown formatting like ```json.
            6.  JSON Structure: Each MCQ object in the list must strictly follow this structure:
                {{
                    "question": "The question text in {language.upper()}",
                    "options": {{
                        "A": "Option A text in {language.upper()}",
                        "B": "Option B text in {language.upper()}",
                        "C": "Option C text in {language.upper()}",
                        "D": "Option D text in {language.upper()}"
                    }},
                    "correct_answer": "LETTER"
                }}
                - Replace "LETTER" with the single capital letter (A, B, C, or D) of the correct option.
                - Ensure keys are exactly "question", "options", "correct_answer".
                - The value for "options" must be a JSON object (dictionary).

            Extract and format MCQs from the image now in the specified JSON format.
            """
            
            # Create the complete multipart content
            content_parts = [
                {"text": text_prompt},
                {"inline_data": image_parts[0]}
            ]
            
            # Generation config - lower temperature for consistency
            generation_config = genai.types.GenerationConfig(temperature=0.2)
            
            # Generate content
            print("Sending request to Gemini with image...")
            response = model.generate_content(content_parts, generation_config=generation_config)
            
            # Process response
            if not response.candidates:
                print("ERROR: Gemini response blocked or empty")
                return None
                
            raw_text = response.text
            print(f"Received response (preview): {raw_text[:200]}...")
            
            # Parse JSON
            cleaned_json = self.clean_json_response(raw_text)
            if cleaned_json:
                try:
                    mcqs = json.loads(cleaned_json)
                    if isinstance(mcqs, list):
                        print(f"Successfully parsed JSON with {len(mcqs)} items")
                        return mcqs
                    elif isinstance(mcqs, dict):
                        print("Found single MCQ object, wrapping in list")
                        return [mcqs]
                    else:
                        print(f"ERROR: Unexpected JSON structure: {type(mcqs)}")
                        return None
                except json.JSONDecodeError as e:
                    print(f"ERROR: JSON decode failed: {e}")
                    return None
            else:
                print("ERROR: Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"ERROR in Gemini image MCQ extraction: {e}")
            print(traceback.format_exc())
            return None




class EgyptianIDExtractorView(APIView):
    """API View to extract information from Egyptian national ID card images using AI models."""
    parser_classes = (MultiPartParser, FormParser)

    # Configuration constants
    DEFAULT_GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "")
    
    # Available models - only use multimodal models that can process images
    AVAILABLE_MODELS = {
        "gemini-flash": "gemini-1.5-flash-latest",
        "gemini-flash-2": "gemini-2.0-flash",
        "gemini-pro": "gemini-1.5-pro"
    }
    SUPPORTED_LANGUAGES = ["en", "ar"]
    
    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def post(self, request, *args, **kwargs):
        """Handle POST requests to extract information from Egyptian national ID images."""
        # Validate input file
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES['file']
        if file.size > self.MAX_FILE_SIZE:
            return Response({"error": f"File too large. Maximum size is {self.MAX_FILE_SIZE/1024/1024}MB"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        file_extension = os.path.splitext(file.name.lower())[1]
        if file_extension not in self.SUPPORTED_IMAGE_FORMATS:
            return Response(
                {"error": f"Unsupported file format. Supported formats: {', '.join(self.SUPPORTED_IMAGE_FORMATS)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract parameters
        model_option = request.data.get('model', 'gemini-flash').lower()
        language = request.data.get('lang', 'en').lower()

        if model_option not in self.AVAILABLE_MODELS:
            return Response(
                {"error": f"Invalid model option. Available options: {', '.join(self.AVAILABLE_MODELS.keys())}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if language not in self.SUPPORTED_LANGUAGES:
            return Response(
                {"error": f"Invalid language. Supported languages: {', '.join(self.SUPPORTED_LANGUAGES)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_name = self.AVAILABLE_MODELS[model_option]

        # Process file and extract ID information
        temp_path = None
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp:
                for chunk in file.chunks():
                    temp.write(chunk)
                temp_path = temp.name

            # Extract information from ID card image
            print(f"Processing Egyptian National ID image using model: {model_option}, language: {language}")
            
            # Only Gemini models support image input directly
            if model_option.startswith('gemini'):
                id_info = self.extract_id_info_with_gemini(temp_path, model_name, language)
            else:
                return Response(
                    {"error": "Selected model does not support direct image processing. Please use a Gemini model."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate extraction results
            if not id_info or not isinstance(id_info, dict):
                return Response({"error": "Failed to extract information from ID card. Check server logs for details."},
                               status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Return success response
            return Response({
                "message": f"Successfully extracted information from Egyptian National ID card",
                "language": language,
                "model_used": model_name,
                "id_info": id_info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in POST request: {e}")
            print(traceback.format_exc())
            return Response({"error": f"An unexpected server error occurred: {e}"},
                           status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"Error cleaning up temporary file {temp_path}: {e}")

    def clean_json_response(self, raw_text):
        """Extract JSON from model output text."""
        if not raw_text:
            return None

        # Try finding JSON within markdown code blocks
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            potential_json = match.group(1).strip()
            if potential_json.startswith('{') and potential_json.endswith('}'):
                return potential_json

        # Try finding JSON by curly braces
        start_curly = raw_text.find('{')
        if start_curly == -1:
            return None

        end_curly = raw_text.rfind('}')
        if end_curly == -1 or end_curly < start_curly:
            return None

        return raw_text[start_curly:end_curly + 1].strip()

    def extract_id_info_with_gemini(self, image_path, model_name, language='en'):
        """Extract Egyptian National ID information using Google Gemini API."""
        print(f"Extracting Egyptian ID info with Gemini model: {model_name}")
        
        # Get API key
        api_key = os.environ.get('GEMINI_API_KEY', self.DEFAULT_GEMINI_API_KEY)
        if not api_key:
            print("ERROR: Missing Gemini API key")
            return None

        try:
            # Configure API
            genai.configure(api_key=api_key)
            
            # Create model instance with vision capability
            model = genai.GenerativeModel(model_name)
            print(f"Created model instance: {model.model_name}")
            
            # Language-specific instructions
            lang_instructions = {
                "en": "Extract and format the information in English.",
                "ar": "Extract and format the information in Arabic."
            }
            
            # Read image file
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # Create multimodal prompt with image and text instructions
            image_parts = [
                {
                    "mime_type": f"image/{os.path.splitext(image_path)[1][1:]}",
                    "data": base64.b64encode(image_data).decode("utf-8")
                }
            ]
            
            text_prompt = f"""
            Look at this image of an Egyptian National ID card.

            Task:
            Extract the following information from the ID card:
            1. Full name (in both Arabic and English if available)
            2. National ID number (14-digit number)
            3. Birth date (in the format shown on the card)
            4. Address (if visible)
            5. Gender
            6. Card expiration date (if visible)
            7. Religion (if visible)
            8. Marital status (if visible)
            9. Profession/job (if visible)

            Instructions:
            1. Be precise and extract only information that is clearly visible in the image.
            2. For text in Arabic, carefully transcribe it.
            3. If any field is not visible or unclear, mark it as "Not visible" or "Unclear".
            4. {lang_instructions.get(language, lang_instructions["en"])}
            5. The ID number should be extracted completely and accurately - this is critical.
            6. Output Format: Respond ONLY with a valid JSON object. Do NOT include any text before the opening curly brace '{{' or after the closing curly brace '}}'. Do not use markdown formatting like ```json.
            7. JSON Structure: The output must strictly follow this structure:
            {{
                "full_name": "The person's full name",
                "national_id": "14-digit national ID number",
                "birth_date": "Date of birth as shown on card",
                "address": "Address as shown on card",
                "gender": "Male or Female",
                "expiration_date": "Card expiration date if visible",
                "religion": "Religion if visible",
                "marital_status": "Marital status if visible",
                "profession": "Profession/job if visible"
            }}

            Extract the information from the Egyptian ID card now in the specified JSON format.
            """
            
            # Create the complete multipart content
            content_parts = [
                {"text": text_prompt},
                {"inline_data": image_parts[0]}
            ]
            
            # Generation config - low temperature for factual extraction
            generation_config = genai.types.GenerationConfig(temperature=0.1)
            
            # Generate content
            print("Sending request to Gemini with ID card image...")
            response = model.generate_content(content_parts, generation_config=generation_config)
            
            # Process response
            if not response.candidates:
                print("ERROR: Gemini response blocked or empty")
                return None
                
            raw_text = response.text
            print(f"Received response (preview): {raw_text[:200]}...")
            
            # Parse JSON
            cleaned_json = self.clean_json_response(raw_text)
            if cleaned_json:
                try:
                    id_info = json.loads(cleaned_json)
                    if isinstance(id_info, dict):
                        print(f"Successfully parsed ID information JSON")
                        # Additional validation for required fields
                        required_fields = ["full_name", "national_id", "birth_date"]
                        missing_fields = [field for field in required_fields if not id_info.get(field)]
                        if missing_fields:
                            print(f"WARNING: Missing required fields: {', '.join(missing_fields)}")
                        return id_info
                    else:
                        print(f"ERROR: Unexpected JSON structure: {type(id_info)}")
                        return None
                except json.JSONDecodeError as e:
                    print(f"ERROR: JSON decode failed: {e}")
                    return None
            else:
                print("ERROR: Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"ERROR in Gemini ID info extraction: {e}")
            print(traceback.format_exc())
            return None

