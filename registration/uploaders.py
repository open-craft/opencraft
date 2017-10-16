from django_fine_uploader.views import FineUploaderView
from django_fine_uploader.fineuploader import SimpleFineUploader

class RegistrationImagesUploaderView(FineUploaderView):
    """
    Similar view to FineUploaderView but without chunked uploads (disabled because they didn't work due to unmatching paramater names).
    """
    def process_upload(self, form):
        self.upload = SimpleFineUploader(form.cleaned_data, self.concurrent)
        self.upload.save()
