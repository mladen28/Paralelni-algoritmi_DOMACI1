import os
import gzip
import hashlib
import threading
import queue
import yaml
import time
from concurrent.futures import ProcessPoolExecutor

file_registry = {}
file_parts_registry = {}
config = {
    'file_parts_directory': 'directory',
    'chunk_size': 2048,  # 1/2 MB
    'num_workers': 4,
    'max_memory_usage': 1024 * 1024 * 1024,  # 1 GB
    'process_pool_size': 2  # Veličina procesnog bazena
}
yaml_file_path = 'config.yaml'
current_memory_usage = 0
tasks_queue = queue.Queue()
process_pool = ProcessPoolExecutor(config['process_pool_size'])
memory_usage_lock = threading.Lock()
i = 0

with open(yaml_file_path, 'w') as file:
    yaml.dump(config, file, default_flow_style=False)

def md5_hash(data):
    hasher = hashlib.md5()
    hasher.update(data)
    return hasher.hexdigest()

def compress_data(data):
    return gzip.compress(data)

def decompress_data(data):
    return gzip.decompress(data)

def read_and_compress_chunk(file_path, chunk_size, chunk_number):
    with open(file_path, 'rb') as file:
        file.seek(chunk_number * chunk_size)
        data = file.read(chunk_size)
        if not data:
            return None
        return compress_data(data)

def write_decompressed_chunk(part_file_path, output_file_path):
    with open(part_file_path, 'rb') as part_file:
        compressed_data = part_file.read()
    data = decompress_data(compressed_data)
    with open(output_file_path, 'ab') as output_file:
        output_file.write(data)

def worker():
    while True:
        task = tasks_queue.get()
        if task is None:
            break
        command, args = task
        if command == 'put':
            put_file(*args)
        elif command == 'get':
            get_file(*args)
        elif command == 'delete':
            delete_file(*args)
        elif command == 'list':
            list_files()
        elif command == 'exit':
            shutdown_system()
        tasks_queue.task_done()

def put_file(file_path):
    global current_memory_usage,i
    file_size = os.path.getsize(file_path)
    with memory_usage_lock:
        if current_memory_usage + file_size > config['max_memory_usage']:
            print("Not enough memory to process file.")
            return
        current_memory_usage += file_size

    file_name = os.path.basename(file_path)
    file_id = str(i)
    file_parts = []

    try:
        part_num = 0
        total_chunks = file_size // config['chunk_size'] + (1 if file_size % config['chunk_size'] > 0 else 0)
        futures = [process_pool.submit(read_and_compress_chunk, file_path, config['chunk_size'], i) for i in range(total_chunks)]

        j = 0
        for future in futures:
            compressed_data = future.result()
            if compressed_data is None:
                break

            part_hash = md5_hash(compressed_data)
            part_id = str(j)
            j += 1

            part_file_name = f"{file_id}_{part_num}.gz"
            part_file_path = os.path.join(config['file_parts_directory'], part_file_name)
            with open(part_file_path, 'wb') as part_file:
                part_file.write(compressed_data)

            file_parts_registry[part_id] = {
                'file_id': file_id,
                'part_num': part_num,
                'hash': part_hash,
                'size': len(compressed_data)
            }

            file_parts.append(part_id)
            part_num += 1

        file_registry[file_id] = {
            'file_name': file_name,
            'parts': file_parts
        }
        i += 1
    finally:
        with memory_usage_lock:
            current_memory_usage -= file_size
    print(f"File {file_name} added with ID {file_id}")

def get_file(file_id, destination_path):
    if file_id not in file_registry:
        print(f"No file found with ID {file_id}")
        return False

    output_file_path = os.path.join(destination_path, file_registry[file_id]['file_name'])

    try:
        futures = []
        for part_id in file_registry[file_id]['parts']:
            part_info = file_parts_registry[part_id]
            part_file_name = f"{file_id}_{part_info['part_num']}.gz"
            part_file_path = os.path.join(config['file_parts_directory'], part_file_name)

            if not os.path.exists(part_file_path):
                print(f"File part {part_file_path} does not exist.")
                return False

            futures.append(process_pool.submit(write_decompressed_chunk, part_file_path, output_file_path))

        for future in futures:
            future.result()

        print(f"File {file_registry[file_id]['file_name']} has been reconstructed successfully.")
        return True

    except Exception as e:
        print(f"An error occurred: {e}")
        return False
def delete_file(file_id):
    # Provera da li datoteka postoji u registru
    if file_id not in file_registry:
        print(f"No file found with ID {file_id}")
        return False

    try:
        # Uklanjanje svih delova datoteke sa diska
        for part_id in file_registry[file_id]['parts']:
            part_info = file_parts_registry[part_id]
            part_file_name = f"{file_id}_{part_info['part_num']}.gz"
            part_file_path = os.path.join(config['file_parts_directory'], part_file_name)

            if os.path.exists(part_file_path):
                os.remove(part_file_path)
                print(f"Deleted part {part_file_name}")

        # Uklanjanje podataka o datoteci iz globalnih registara
        del file_registry[file_id]
        for part_id in list(file_parts_registry):
            if file_parts_registry[part_id]['file_id'] == file_id:
                del file_parts_registry[part_id]

        print(f"File with ID {file_id} and all its parts have been deleted.")
        return True

    except Exception as e:
        print(f"An error occurred while deleting file {file_id}: {e}")
        return False


def list_files():
    # Provera da li postoji bilo koja datoteka u registru
    if not file_registry:
        print("No files found.")
        return

    # Ispisivanje informacija o svakoj datoteci
    for file_id, file_info in file_registry.items():
        print(f"File ID: {file_id}")
        print(f"\tFile Name: {file_info['file_name']}")
        print(f"\tNumber of Parts: {len(file_info['parts'])}")

        print("\tParts:")
        for part_id in file_info['parts']:
            part = file_parts_registry[part_id]
            print(f"\t\tPart Number: {part['part_num']} Size: {part['size']} Hash: {part['hash']}")

def load_config(config_path):
    global config
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

def shutdown_system():
    for _ in range(config['num_workers']):
        tasks_queue.put(None)
def main():
    threads = []
    load_config('config.yaml')
    for _ in range(config['num_workers']):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    while True:
        time.sleep(1)
        command = input("Enter command: ")
        if command == 'exit':
            for i in range(config['num_workers']):
                tasks_queue.put(('exit', []))
            break
        elif command.startswith('put '):
            file_path = command.split(' ', 1)[1]
            tasks_queue.put(('put', [file_path]))
        elif command.startswith('get '):
            file_id, destination_path = command.split(' ')[1:]
            tasks_queue.put(('get', [file_id, destination_path]))
        elif command.startswith('delete '):
            file_id = command.split(' ', 1)[1]
            tasks_queue.put(('delete', [file_id]))
        elif command == 'list':
            tasks_queue.put(('list', []))
        else:
            print("Unknown command")

    for t in threads:
        t.join()

if __name__ == "__main__":
    main()