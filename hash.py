'''
获取模型哈希值
'''
import hashlib
import folder_paths
def calculate_hash(name, hash_type):
    match hash_type:
        case "model":
            # hash_dict = A1111SaveImage.model_hash_dict
            file_name = folder_paths.get_full_path("checkpoints", name)
        case "vae":
            # hash_dict = A1111SaveImage.vae_hash_dict
            file_name = folder_paths.get_full_path("vae", name)
        case "lora":
            # hash_dict = A1111SaveImage.lora_hash_dict
            file_name = folder_paths.get_full_path("loras", name)
        case "ti":
            # hash_dict = A1111SaveImage.ti_hash_dict
            file_name = folder_paths.get_full_path("embeddings", name)
        case _:
            return ""

    # if hash_value := hash_dict.get(name):
    #     return hash_value

    hash_sha256 = hashlib.sha256()
    blksize = 1024 * 1024

    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(blksize), b""):
            hash_sha256.update(chunk)

    hash_value = hash_sha256.hexdigest()[:10]
    # hash_dict[name] = hash_value
    print(name, hash_sha256.hexdigest(), hash_value)
    return hash_value


model_path = "/data/wenshengtu/sdFile/models/Lora"
model_list = os.listdir(model_path)
for model in model_list:
    calculate_hash(model, 'lora')

