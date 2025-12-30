"""
Load generated test data into the API
"""
import requests
import json
import time
from typing import Dict, List

API_URL = "http://localhost:8000"  # Change to your API URL


def load_data(filename: str = "test_data_medium.json"):
    """Load test data from JSON file and upload to API"""
    print(f"Loading test data from {filename}...")
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} clients to upload")
    
    total_clients = 0
    total_documents = 0
    start_time = time.time()
    
    for i, client_data in enumerate(data):
        # Create client
        try:
            response = requests.post(
                f"{API_URL}/clients",
                json=client_data["client"]
            )
            
            if response.status_code == 201:
                client_id = response.json()["id"]
                total_clients += 1
                
                # Create documents for this client
                documents = client_data["documents"]
                
                # Batch upload (faster - uses batch embedding generation)
                try:
                    batch_response = requests.post(
                        f"{API_URL}/clients/{client_id}/documents/batch",
                        json={"documents": documents}
                    )
                    if batch_response.status_code == 201:
                        total_documents += len(documents)
                    else:
                        # Fallback to one-by-one if batch fails
                        print(f"  ⚠ Batch upload failed ({batch_response.status_code}), falling back to individual uploads")
                        for doc in documents:
                            doc_response = requests.post(
                                f"{API_URL}/clients/{client_id}/documents",
                                json=doc
                            )
                            if doc_response.status_code == 201:
                                total_documents += 1
                except Exception as e:
                    # Fallback to one-by-one if batch fails
                    print(f"  ⚠ Batch upload error: {e}, falling back to individual uploads")
                    for doc in documents:
                        doc_response = requests.post(
                            f"{API_URL}/clients/{client_id}/documents",
                            json=doc
                        )
                        if doc_response.status_code == 201:
                            total_documents += 1
                
                if (i + 1) % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = (i + 1) / elapsed
                    print(f"  Uploaded {i + 1}/{len(data)} clients ({rate:.1f} clients/sec)")
            
            else:
                print(f"  ✗ Failed to create client: {response.status_code}")
        
        except Exception as e:
            print(f"  ✗ Error creating client: {e}")
            continue
    
    elapsed = time.time() - start_time
    
    print(f"\n✓ Upload complete!")
    print(f"  Clients created: {total_clients}")
    print(f"  Documents created: {total_documents}")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Average rate: {total_clients/elapsed:.1f} clients/sec, {total_documents/elapsed:.1f} docs/sec")


if __name__ == "__main__":
    import sys
    
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_data_medium.json"
    load_data(filename)