import csv
import io
import os
from datetime import datetime

class ReportingService:
    def generate_invoice_csv(self, invoices_data: list) -> str:
        """
        Generates a CSV string from a list of invoice dictionaries.
        Uses standard library 'csv' to avoid heavy dependencies like pandas.
        """
        if not invoices_data:
            return ""
            
        output = io.StringIO()
        # Get headers from the first dictionary keys
        headers = list(invoices_data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(invoices_data)
        
        return output.getvalue()

reporting_service = ReportingService()
