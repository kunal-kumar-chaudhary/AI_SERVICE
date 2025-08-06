from supabase import create_client, Client
import os
import requests

supabase: Client = create_client(
    os.getenv("NEXT_PUBLIC_SUPABASE_URL"),
    os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
)

def get_file_from_supabase_storage(bucket_name: str, file_url: str):
    response = supabase.storage.from_(bucket_name).download(file_url)
    return response


