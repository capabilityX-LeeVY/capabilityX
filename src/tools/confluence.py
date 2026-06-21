import requests
import json
import markdown

from pathlib import Path


class ConfluenceCreator(object):
    def __init__(self, confluence_token="MTk2NjgwNzY5ODU0Om8NfQY1SmtEYZjAsfvQsOPLUMu5", space_key="WMT", base_url="https://confluence-eng-gpk2.cisco.com/conf"):
        self.base_url = base_url
        self.confluence_token = confluence_token
        self.space_key = space_key

    def get_page_id_by_title(self, space_key, title):
        url = f"{self.base_url}/rest/api/content"
        params = {"title": title, "spaceKey": space_key}
        headers = {"Authorization": f"Bearer {self.confluence_token}", "Accept": "application/json"}
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                return results[0]["id"]
        print(f"❌ Cannot find page '{title}' in space {space_key}")
        return None

    def upload_attachment(self, page_id, file_path):
        url = f"{self.base_url}/rest/api/content/{page_id}/child/attachment"
        headers = {
            "Authorization": f"Bearer {self.confluence_token}",
            "X-Atlassian-Token": "no-check"
        }
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, headers=headers, files=files)
        
        if response.status_code in (200, 201):
            result = response.json()
            attachment_id = result["results"][0]["id"]
            print(f"✅ Uploaded {file_path} to page {page_id}, attachment_id={attachment_id}")
            return attachment_id
        else:
            print(f"❌ Failed to upload {file_path}: {response.status_code}, {response.text}")
            return None

    def create_page(self, title, body, parent=None):
        parent_id = None
        if parent:
            if "/" in parent:
                space_key, parent_title = parent.split("/", 1)
            else:
                space_key = self.space_key
                parent_title = parent
            parent_id = self.get_page_id_by_title(space_key, parent_title)
            if parent_id is None:
                print(f"❌ Parent page '{parent}' not found. Page '{title}' will not be created.")
                return None, None

        url = f"{self.base_url}/rest/api/content"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.confluence_token}"
        }
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": self.space_key},
            "body": {"storage": {"value": body, "representation": "storage"}}
        }
        if parent_id:
            payload["ancestors"] = [{"id": str(parent_id)}]

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code in (200, 201):
            result = response.json()
            page_id = result["id"]
            link = result["_links"]["base"] + result["_links"]["webui"]
            print(f"✅ Confluence page created: {link}")
            return page_id, link
        else:
            print(f"❌ Failed to create page: {response.status_code}, {response.text}")
            return None, None

    def update_page(self, page_id, title, body):
        get_url = f"{self.base_url}/rest/api/content/{page_id}?expand=version"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.confluence_token}"
        }
        resp = requests.get(get_url, headers=headers)
        if resp.status_code != 200:
            print(f"❌ Failed to fetch page {page_id}: {resp.status_code}, {resp.text}")
            return None

        current_version = resp.json()["version"]["number"]

        url = f"{self.base_url}/rest/api/content/{page_id}"
        headers.update({"Content-Type": "application/json"})
        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "body": {"storage": {"value": body, "representation": "storage"}},
            "version": {"number": current_version + 1}
        }

        response = requests.put(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            result = response.json()
            link = result["_links"]["base"] + result["_links"]["webui"]
            print(f"✅ Confluence page updated: {link}")
            return link
        else:
            print(f"❌ Failed to update page {page_id}: {response.status_code}, {response.text}")
            return None

    # def create_page_with_pdf(self, title, body, pdf_path, parent=None):
    #     page_id, link = self.create_page(title, body, parent)
    #     if not page_id:
    #         return None, None

    #     if Path(pdf_path).exists():
    #         attachment_id = self.upload_attachment(page_id, pdf_path)
    #         if attachment_id:
    #             updated_body = f"""
    #             {body}
    #             <p>PDF：</p>
    #             <ac:structured-macro ac:name="view-file">
    #                 <ac:parameter ac:name="name">{Path(pdf_path).name}</ac:parameter>
    #                 <ac:parameter ac:name="atlassian-attachment-id">{attachment_id}</ac:parameter>
    #             </ac:structured-macro>
    #             """
    #             self.update_page(page_id, title, updated_body)
    #     else:
    #         print(f"❌ PDF not found: {pdf_path}")

    #     return page_id, link

    def _add_attachment_with_info(self, page_id, title, body, filename):
        try:
            enhanced_body = f"""
            {body}
            
            <hr/>
            <h3>📋 Related Documents</h3>
            <p><strong>File:</strong> {filename}</p>
            <p><strong>Note:</strong> Click the file name to download or preview</p>
            
            <ac:structured-macro ac:name="attachments" ac:schema-version="1">
                <ac:parameter ac:name="patterns">{filename}</ac:parameter>
                <ac:parameter ac:name="sortBy">name</ac:parameter>
            </ac:structured-macro>
            """
            self.update_page(page_id, title, enhanced_body)
            print("✅ Page updated with attachment list and file info")
        except Exception as e:
            print(f"❌ Failed to add attachment info: {e}")
            try:
                simple_body = f"""
                {body}
                <p>📎 Attachment: <strong>{filename}</strong> (Please check the attachments section at the top of the page)</p>
                """
                self.update_page(page_id, title, simple_body)
                print("✅ Page updated with simple attachment note")
            except Exception as e2:
                print(f"❌ Even simple update failed: {e2}")

    def set_page_with_pdf(self, title, body, pdf_path, parent=None):
        page_id = self.get_page_id_by_title(self.space_key, title)
        if page_id:
            link = self.update_page(page_id, title, body)
        else:
            page_id, link = self.create_page(title, body, parent)
            if not page_id:
                return None, None

        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            print(f"Uploading attachment: {pdf_file}")
            attachment_id = self.upload_attachment(page_id, str(pdf_file))
            if attachment_id:
                print(f"Attachment ID: {attachment_id}")
                self._add_attachment_with_info(page_id, title, body, pdf_file.name)
            else:
                print("❌ Failed to upload attachment.")
        else:
            print(f"❌ PDF not found: {pdf_file}")

        return page_id, link

    def set_page_with_image(self, title, body, image_path, parent=None):
        page_id = self.get_page_id_by_title(self.space_key, title)
        if page_id:
            link = self.update_page(page_id, title, body)
        else:
            page_id, link = self.create_page(title, body, parent)
            if not page_id:
                return None, None

        image_file = Path(image_path)
        if image_file.exists():
            attachment_id = self.upload_attachment(page_id, str(image_file))
            if attachment_id:
                img_url = f"{self.base_url}/download/attachments/{page_id}/{image_file.name}"
                
                updated_body = f"""
                {body}
                <p>Image:</p>
                <img src="{img_url}" />
                """
                self.update_page(page_id, title, updated_body)
        else:
            print(f"❌ Image not found: {image_file}")

        return page_id, link


    def set_page_with_markdown(self, title, md_file_path, parent=None):
        md_file = Path(md_file_path)
        if not md_file.exists():
            print(f"❌ Markdown file not found: {md_file}")
            return None, None
        with open(md_file, "r", encoding="utf-8") as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

        page_id = self.get_page_id_by_title(self.space_key, title)
        if page_id:
            link = self.update_page(page_id, title, html_content)
            return page_id, link
        else:
            return self.create_page(title, html_content, parent)



if __name__ == "__main__":
    token = "MjAyOTgyMjc2MTM3Oq65loLbkytb1ELAJclSXbETyr6W"
    cc = ConfluenceCreator(confluence_token=token)
    title = f"Test Page for img - weiqin"
    body = "<h1>This is a test page</h1><p>Created via API</p>"
    attachment_file = Path("/Users/weiqli/Downloads/20250729-094151/dashboard_4.png")
    cc.set_page_with_image(title, body, attachment_file, parent="WRS report")
    # cc.set_page_with_pdf(title, body, attachment_file, parent="WRS report - test")
    # cc.set_page_with_markdown(title, attachment_file, parent="WRS report")

