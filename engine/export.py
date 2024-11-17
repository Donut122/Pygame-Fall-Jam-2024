# """pyinstaller game_runner.py -w --onefile --add-data="assets;assets" --add-data="scaling_info.json;scaling_info.json" """

import os
import shutil
return_value = os.system("""pyinstaller main.py -w --onefile""")
if return_value == 0:
    print("successfully built executable, adding assets to dist")

    shutil.copytree("assets", "dist/assets")

    print("Success :D")
else: print("Fail D:")