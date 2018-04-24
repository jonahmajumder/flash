import os

cwd = os.getcwd()

def get_file_list(cwd, files=[], exclude=[]):
    file_list = os.listdir(cwd)
    for file in file_list:
        full_path = cwd + '/' + file
        if not os.path.isdir(full_path):
            if file not in exclude:
                files.append(full_path.replace((cwd + '/'), ''))
        else:
            if file not in exclude:
                files = get_file_list(full_path, files, exclude)
    return file_list

if __name__ == '__main__':
    print get_files(cwd, [])