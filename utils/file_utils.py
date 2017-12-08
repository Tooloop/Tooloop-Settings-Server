import os, shutil

def clear_folder(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            raise

# def copy_dir_contents(folder, destination):
#     for the_file in os.listdir(folder):
#         file_path = os.path.join(folder, the_file)
#         try:
#             if os.path.isfile(file_path):
#                 shutil.copy(file_path, destination)
#             elif os.path.isdir(file_path): shutil.rmtree(file_path)
#         except Exception as e:
#             raise
