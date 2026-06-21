import ftplib
import os
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

class FTPHandler:
    def __init__(self, server, username, password):
        self.server = server
        self.username = username
        self.password = password
        self.ftp = None

    def connect(self):
        try:
            self.ftp = ftplib.FTP(self.server)
            self.ftp.login(self.username, self.password)
            LOGGER_INFO(f"Connected to FTP server: {self.server}")
        except Exception as e:
            LOGGER_ERROR(f"Error connecting to FTP server: {e}")

    def disconnect(self):
        if self.ftp:
            self.ftp.quit()
            LOGGER_INFO(f"Disconnected from FTP server: {self.server}")

    def upload_file(self, local_file_path, remote_file_path):
        if self.ftp is None:
            LOGGER_INFO("FTP connection is not established.")
            return

        try:
            remote_dir, remote_file = os.path.split(remote_file_path)
            self._ensure_remote_directory(remote_dir)

            with open(local_file_path, 'rb') as file:
                self.ftp.storbinary(f'STOR {remote_file}', file)
            LOGGER_INFO(f"File '{local_file_path}' uploaded successfully to '{remote_file_path}'")
        except Exception as e:
            LOGGER_ERROR(f"Error uploading file: {e}")

    def delete_file(self, remote_file_path):
        if self.ftp is None:
            LOGGER_ERROR("FTP connection is not established.")
            return

        try:
            self.ftp.delete(remote_file_path)
            LOGGER_INFO(f"File '{remote_file_path}' deleted successfully")
        except Exception as e:
            LOGGER_ERROR(f"Error deleting file: {e}")

    def _ensure_remote_directory(self, remote_dir):
        if self.ftp is None:
            LOGGER_ERROR("FTP connection is not established.")
            return

        try:
            self.ftp.cwd(remote_dir)
        except ftplib.error_perm:
            dirs = remote_dir.split('/')
            path = ''
            for dir in dirs:
                path = f"{path}/{dir}" if path else dir
                try:
                    self.ftp.cwd(path)
                except ftplib.error_perm:
                    self.ftp.mkd(path)
                    self.ftp.cwd(path)


# Example usage
if __name__ == "__main__":
    ftp_handler = FTPHandler('wrs.qa.webex.com', 'ftpuser', 'P@ss1234')
    ftp_handler.connect()
    ftp_handler.upload_file(r'src\report\navigation\acc-navigation-report-44.11.0.30797.md', 'navigation/acc-navigation-report-44.11.0.30797.md')
    # ftp_handler.delete_file('navigation/acc-navigation-report-44.11.0.30797.md')
    ftp_handler.disconnect()