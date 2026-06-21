import requests
import os
import io

from PIL import Image
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from prompts.prompt_loader import load_prompt, OCRPrompts

# Maximum image file size (in bytes) before JPEG compression is applied
_MAX_IMAGE_SIZE_BYTES = 1 * 1024 * 1024  # 1 MB

class OpenAIClient:
    def __init__(self) -> None:
        self.BASE_URL = "http://gc-hgh05-level2-lab-irc-5.cisco.com:9912/gpt"
        self.IMAGE_COMPARISON_ENDPOINT = "/analyze_image_comparison/"
        self.IMAGE_ANALYZE_ENDPOINT = "/analyze_image/"
        self.CHAT_ENDPOINT = "/chat/"
        self.CHAT_I18N_ENDPOINT = "/chat_i18n/"
        self.CHAT_SR_ENDPOINT = "/chat_sr/"
        self.ANALYZE_PERFORMANCE_ENDPOINT = "/analyze_performance/"
    
    def _get_endpoint_url(self, endpoint):
        """Helper method to construct full URL"""
        return f"{self.BASE_URL}{endpoint}"

    @staticmethod
    def _compress_image_for_upload(image_path, quality=85):
        """Compress image to JPEG if it exceeds the upload size limit.

        Returns a tuple suitable for ``requests`` *files* parameter:
        ``(filename, file_object, content_type)``.
        The caller is responsible for closing the returned file object.
        """
        file_size = os.path.getsize(image_path)
        if file_size <= _MAX_IMAGE_SIZE_BYTES:
            return open(image_path, "rb")

        LOGGER_INFO(
            f"[image compress] Image {os.path.basename(image_path)} is {file_size / 1024:.0f} KB, "
            f"compressing to JPEG (quality={quality})",
            "YELLOW",
        )
        img = Image.open(image_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        buf.seek(0)
        compressed_name = os.path.splitext(os.path.basename(image_path))[0] + ".jpg"
        LOGGER_INFO(
            f"[image compress] Compressed size: {buf.getbuffer().nbytes / 1024:.0f} KB",
            "YELLOW",
        )
        return (compressed_name, buf, "image/jpeg")

    def ai_analyze_image(self, image_path, message=None):
        """
        Analyze a single image using AI.
        
        Args:
            image_path (str): Path to the image file to analyze
            message (str, optional): Additional message or context for the analysis
            
        Returns:
            str: Analysis result from the API, or None if failed
        """
        # Prepare files (compress large images to JPEG before upload)
        files = {}
        img_handle = None
        if image_path and os.path.exists(image_path):
            img_handle = self._compress_image_for_upload(image_path)
            files["image"] = img_handle
        else:
            files["image"] = ('', b'')
            
        # Prepare data
        data = {}
        if message is not None:
            data["message"] = message
            
        response = requests.post(self._get_endpoint_url(self.IMAGE_ANALYZE_ENDPOINT), files=files, data=data)

        # Close file handle
        if img_handle is not None:
            if isinstance(img_handle, tuple):
                img_handle[1].close()
            else:
                img_handle.close()

        # Parse the response and extract only the 'Output' part from the 'result' field
        try:
            LOGGER_DEBUG(f"ai_analyze_image API response status: {response.status_code}", "BLUE")
            LOGGER_DEBUG(f"ai_analyze_image API response headers: {response.headers}", "BLUE")
            
            result = response.json().get("result", "")
            LOGGER_DEBUG(f"ai_analyze_image Raw API result field: '{result}'", "BLUE")
            
            if result.startswith("Output:"):
                result = result[len("Output:"):].strip()
            LOGGER_INFO(f"ai_analyze_image Final processed result: '{result}'", "GREEN")
            return result
        except Exception as e:
            LOGGER_ERROR(f"Failed to parse response: {e}", "RED")
            return None

    def chat_i18n(self, image_path, message=None):
        """
        Analyze a single image using AI.
        
        Args:
            image_path (str): Path to the image file to analyze
            message (str, optional): Additional message or context for the analysis
            
        Returns:
            str: Analysis result from the API, or None if failed
        """
        # Prepare files (compress large images to JPEG before upload)
        files = {}
        img_handle = None
        if image_path and os.path.exists(image_path):
            img_handle = self._compress_image_for_upload(image_path)
            files["image"] = img_handle
        else:
            files["image"] = ('', b'')
            
        # Prepare data
        data = {}
        if message is not None:
            data["message"] = message

        response = requests.post(self._get_endpoint_url(self.CHAT_I18N_ENDPOINT), files=files, data=data)

        # Close file handle
        if img_handle is not None:
            if isinstance(img_handle, tuple):
                img_handle[1].close()
            else:
                img_handle.close()

        # Parse the response and extract only the 'Output' part from the 'result' field
        try:
            LOGGER_INFO(f"chat_i18n API response status: {response.status_code}", "BLUE")

            result = response.json().get("result", "")
            LOGGER_INFO(f"chat_i18n Raw API result field: '{result}'", "BLUE")

            if result.startswith("Output:"):
                result = result[len("Output:"):].strip()
            LOGGER_INFO(f"chat_i18n Final processed result: '{result}'", "GREEN")
            return result
        except Exception as e:
            LOGGER_ERROR(f"Failed to parse response: {e}", "RED")
            LOGGER_ERROR(f"Response text: {response.text[:500]}", "RED")
            return None

    def ai_analyze_image_comparison(self, reference_image, target_image, message=None):
        # Compress large images before upload
        files = {}
        ref_handle = None
        tgt_handle = None
        if reference_image and os.path.exists(reference_image):
            ref_handle = self._compress_image_for_upload(reference_image)
            files["reference_image"] = ref_handle
        else:
            files["reference_image"] = ('', b'')
        if target_image and os.path.exists(target_image):
            tgt_handle = self._compress_image_for_upload(target_image)
            files["target_image"] = tgt_handle
        else:
            files["target_image"] = ('', b'')
        data = {}
        if message is not None:
            data["message"] = message
        response = requests.post(self._get_endpoint_url(self.IMAGE_COMPARISON_ENDPOINT), files=files, data=data)

        # Close file handles
        for handle in (ref_handle, tgt_handle):
            if handle is not None:
                if isinstance(handle, tuple):
                    handle[1].close()
                else:
                    handle.close()

        # Parse the response and extract only the 'Output' part from the 'result' field
        try:
            LOGGER_DEBUG(f"ai_analyze_image_comparison API response status: {response.status_code}", "BLUE")
            LOGGER_DEBUG(f"ai_analyze_image_comparison API response headers: {response.headers}", "BLUE")
            
            result = response.json().get("result", "")
            LOGGER_DEBUG(f"ai_analyze_image_comparison Raw API result field: '{result}'", "BLUE")
            
            if result.startswith("Output:"):
                result = result[len("Output:"):].strip()
            LOGGER_INFO(f"ai_analyze_image_comparison Final processed result: '{result}'", "GREEN")
            return result
        except Exception as e:
            LOGGER_ERROR(f"Failed to parse response: {e}", "RED")
            LOGGER_ERROR(f"Response status: {response.status_code}, Response text: {response.text[:500]}", "RED")
            return None


    def chat(self, message):
        """
        Send a chat message to the AI service server.
        
        Args:
            message (str): The message to send to the chat service
            
        Returns:
            str: Response from the chat service, or None if failed
        """
        try:
            # Use GET request with message parameter as per your server implementation
            params = {"message": message}
            response = requests.get(self._get_endpoint_url(self.CHAT_ENDPOINT), params=params)
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.text
                LOGGER_INFO(f"Chat response: {response.status_code}", "GREEN")
                return result
            else:
                LOGGER_ERROR(f"Chat request failed with status {response.status_code}", "RED")
                return None
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to send chat message: {e}", "RED")
            return None

    def compare_ui_with_sr_data(self, ui_report_path, sr_data_path, prompt_template=None, custom_message=None):
        """
        Use LLM to compare UI elements report with Screen Reader data and generate comparison results.
        
        This method reads both the UI elements report and Screen Reader data file, sends them to
        the LLM for intelligent comparison, and returns the updated report with SR Status,
        SR Description, and Similarity columns filled.
        
        Args:
            ui_report_path (str): Path to the UI elements markdown report file
            sr_data_path (str): Path to the Screen Reader data markdown file
            prompt_template (str, optional): Path to prompt template file.
                                            Defaults to 'ocr/ui_sr_comparison.md'
            custom_message (str, optional): Custom prompt message. If provided,
                                           overrides prompt_template
        
        Returns:
            str: Updated markdown table with comparison results, or None if failed
        
        Example:
            # Use default comparison template
            result = client.compare_ui_with_sr_data(
                'reports/ui_elements_20241023.md',
                'data/Windows_level01_1.md'
            )
            
            # Use custom template
            result = client.compare_ui_with_sr_data(
                'reports/ui_elements_20241023.md',
                'data/Windows_level01_1.md',
                prompt_template='ocr/custom_comparison.md'
            )
        """
        try:
            from prompts.prompt_loader import load_prompt, OCRPrompts
            
            # Read UI report file
            if not os.path.exists(ui_report_path):
                LOGGER_ERROR(f"UI report file not found: {ui_report_path}", "RED")
                return None
                
            with open(ui_report_path, 'r', encoding='utf-8') as f:
                ui_report_content = f.read()
            
            # Read SR data file
            if not os.path.exists(sr_data_path):
                LOGGER_ERROR(f"Screen Reader data file not found: {sr_data_path}", "RED")
                return None
                
            with open(sr_data_path, 'r', encoding='utf-8') as f:
                sr_data_content = f.read()
            
            # Determine the prompt message to use
            if custom_message:
                prompt_instruction = custom_message
            elif prompt_template:
                try:
                    prompt_instruction = load_prompt(prompt_template)
                except FileNotFoundError:
                    LOGGER_ERROR(f"Prompt template not found: {prompt_template}", "RED")
                    return None
            else:
                # Use default UI-SR comparison template
                try:
                    prompt_instruction = load_prompt(OCRPrompts.UI_SR_COMPARISON)
                except FileNotFoundError:
                    LOGGER_ERROR("Default UI-SR comparison prompt template not found", "RED")
                    return None
            
            # Build the complete message with instruction + data
            complete_message = f"""{prompt_instruction}

---

## UI Elements Report Content:

{ui_report_content}

---

## Screen Reader Data Content:

{sr_data_content}

---

Please analyze the above data and return the complete comparison table with SR Status, SR Description, and Similarity columns filled for all UI elements.
"""
            
            LOGGER_INFO("🤖 Sending comparison request to LLM...", "BLUE")
            LOGGER_DEBUG(f"Message length: {len(complete_message)} characters", "YELLOW")
            
            # Use the chat method to interact with LLM
            result = self.chat(complete_message)
            
            if result:
                # Clean up markdown code fences if present
                # Remove ```markdown at start and ``` at end
                cleaned_result = result.strip()
                if cleaned_result.startswith('```markdown'):
                    cleaned_result = cleaned_result[len('```markdown'):].strip()
                elif cleaned_result.startswith('```'):
                    cleaned_result = cleaned_result[3:].strip()
                
                if cleaned_result.endswith('```'):
                    cleaned_result = cleaned_result[:-3].strip()
                
                LOGGER_INFO("✅ LLM comparison completed successfully", "GREEN")
                LOGGER_DEBUG(f"Result preview:\n{cleaned_result[:500]}...", "YELLOW")
                
                return cleaned_result
            else:
                LOGGER_ERROR("❌ LLM comparison failed", "RED")
                return None
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to compare UI with SR data: {e}", "RED")
            return None

    def extract_ui_elements(self, image_path, prompt_template=None, custom_message=None):
        """
        Extract UI elements from a screenshot image using OCR analysis.
        
        This method analyzes UI screenshots to identify and extract all visible
        UI elements including buttons, text fields, icons, tabs, etc.
        
        Args:
            image_path (str): Path to the screenshot image file
            prompt_template (str, optional): Path to prompt template file.
                                            Defaults to 'ocr/ui_elements_extraction.md'
                                            Can also use OCRPrompts.UI_ELEMENTS_EXTRACTION
            custom_message (str, optional): Custom prompt message. If provided,
                                           overrides prompt_template
        
        Returns:
            str: Markdown table of extracted UI elements, or None if failed
        
        Example:
            # Use default UI elements extraction template
            result = client.extract_ui_elements('screenshot.png')
            
            # Use custom template
            result = client.extract_ui_elements(
                'screenshot.png',
                prompt_template='ocr/custom_template.md'
            )
            
            # Use custom message
            result = client.extract_ui_elements(
                'screenshot.png',
                custom_message='Extract all button elements only'
            )
        """
        # Determine the message to use
        if custom_message:
            message = custom_message
        elif prompt_template:
            try:
                message = load_prompt(prompt_template)
            except FileNotFoundError:
                LOGGER_ERROR(f"Prompt template not found: {prompt_template}", "RED")
                return None
        else:
            # Use default UI elements extraction template
            try:
                message = load_prompt(OCRPrompts.UI_ELEMENTS_EXTRACTION)
            except FileNotFoundError:
                LOGGER_ERROR("Default OCR prompt template not found", "RED")
                return None
        
        # Use the existing ai_analyze_image method
        result = self.ai_analyze_image(image_path, message=message)
        
        if result:
            LOGGER_INFO("UI elements extracted successfully", "GREEN")
        else:
            LOGGER_WARNING("UI elements extraction returned empty result", "YELLOW")
        
        return result
    
    def extract_text_simple(self, image_path, prompt_template=None, custom_message=None):
        """
        Extract text from an image using simple text extraction.
        
        This method extracts all visible text while preserving layout and structure.
        
        Args:
            image_path (str): Path to the image file
            prompt_template (str, optional): Path to prompt template file.
                                            Defaults to 'ocr/text_extraction_simple.md'
            custom_message (str, optional): Custom prompt message. If provided,
                                           overrides prompt_template
        
        Returns:
            str: Extracted text content, or None if failed
        
        Example:
            # Use default simple text extraction
            text = client.extract_text_simple('document.png')
            
            # Use custom template
            text = client.extract_text_simple(
                'document.png',
                prompt_template='ocr/my_template.md'
            )
        """
        # Determine the message to use
        if custom_message:
            message = custom_message
        elif prompt_template:
            try:
                message = load_prompt(prompt_template)
            except FileNotFoundError:
                LOGGER_ERROR(f"Prompt template not found: {prompt_template}", "RED")
                return None
        else:
            # Use default simple text extraction template
            try:
                message = load_prompt(OCRPrompts.TEXT_EXTRACTION_SIMPLE)
            except FileNotFoundError:
                LOGGER_ERROR("Default text extraction prompt template not found", "RED")
                return None
        
        # Use the existing ai_analyze_image method
        result = self.ai_analyze_image(image_path, message=message)
        
        if result:
            LOGGER_INFO("Text extracted successfully", "GREEN")
        else:
            LOGGER_WARNING("Text extraction returned empty result", "YELLOW")
        
        return result
        
    def chat_sr(self, file_path, message=None):
        """
        Send a markdown file to the AI service server for screen reader analysis.
        
        Args:
            file_path (str): Path to the markdown file to be analyzed
            message (str, optional): Prompt instructions to prepend to the file content.
                                     When provided, the prompt is embedded at the top of the
                                     uploaded content to guide the AI analysis.
            
        Returns:
            str: Response from the chat service, or None if failed
        """
        try:
            with open(file_path, 'rb') as file:
                files = {'markdown_file': file}
                data = {'custom_prompt': message} if message else {}
                response = requests.post(self._get_endpoint_url(self.CHAT_SR_ENDPOINT), files=files, data=data)

            # Check if request was successful
            if response.status_code == 200:
                result = response.text
                LOGGER_INFO(f"Chat response: {response.status_code}", "GREEN")
                return result
            else:
                LOGGER_ERROR(f"Chat request failed with status {response.status_code}", "RED")
                return None
                
        except FileNotFoundError:
            LOGGER_ERROR(f"Markdown file not found: {file_path}", "RED")
            return None
        except Exception as e:
            LOGGER_ERROR(f"Failed to send chat message: {e}", "RED")
            return None

    def analyze_performance(self, file_path=None, markdown_content=None):
        """
        Send performance data to the AI service server for analysis.
        
        Args:
            file_path (str, optional): Path to the markdown file containing performance data
            markdown_content (str, optional): Direct markdown content for analysis
            
        Returns:
            str: Response from the performance analysis service, or None if failed
        """
        try:
            # Option 1: Upload file if file_path is provided
            if file_path and os.path.exists(file_path):
                with open(file_path, 'rb') as file:
                    # Try different parameter names that the server might expect
                    files = {'performance_file': file}
                    response = requests.post(self._get_endpoint_url(self.ANALYZE_PERFORMANCE_ENDPOINT), files=files)
            # Option 2: Send content directly if markdown_content is provided
            elif markdown_content:
                # Try different parameter names for content
                data = {'performance_content': markdown_content}
                response = requests.post(self._get_endpoint_url(self.ANALYZE_PERFORMANCE_ENDPOINT), data=data)
            else:
                LOGGER_ERROR("Either file_path or markdown_content must be provided", "RED")
                return None

            # Check if request was successful
            if response.status_code == 200:
                result = response.text
                LOGGER_INFO(f"Performance analysis response: {response.status_code}", "GREEN")
                return result
            else:
                LOGGER_ERROR(f"Performance analysis request failed with status {response.status_code}", "RED")
                return None
                
        except FileNotFoundError:
            LOGGER_ERROR(f"Performance data file not found: {file_path}", "RED")
            return None
        except Exception as e:
            LOGGER_ERROR(f"Failed to send performance analysis request: {e}", "RED")
            return None

