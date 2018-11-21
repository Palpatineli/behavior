from os.path import join, splitext
from datetime import datetime
from time import sleep
from .windows_clip import paste, is_new

def _extract_name(content: str) -> str:
    line_start = content.find("File : \t")
    file_path = content[line_start + 8: content.find("\n", line_start)]
    return splitext(file_path[file_path.rfind("\\") + 1:])[0]

def _is_valid_name(name: str) -> bool:
    name.replace('-', '_')
    if '_' not in name:
        return False
    date = name.split('_')[-1]
    try:
        datetime.strptime(date, "%Y%m%d")
    except ValueError:
        try:
            datetime.strptime(date, "%m%d%y")
        except ValueError:
            return False
    return True

save_folder = "D:\\Keji\\emka"

def emka_save():
    print("Listening to clipboard")
    while True:
        if is_new():
            content = paste()
            name = _extract_name(content[0: 200])
            if _is_valid_name(name):
                with open(join(save_folder, name + ".txt"), 'w') as fp:
                    fp.write(content)
                print(f"\tsaved file {name}.txt")
        sleep(0.25)
