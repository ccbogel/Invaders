#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Create an output python file called base64_sounds.py
with wav into base64

"""

import base64
import os


class CreateHelperFile:
    """ Important for use with pyinstaller as accessing data files does not work well.
    """

    def __init__(self):

        header = '#!/usr/bin/python\n# -*- coding: utf-8 -*-\n# Generated base64 images helper file\n\n'

        text = header
        tmp_files = os.listdir()
        files = []
        for f in tmp_files:
            if f[-4:] == ".wav":
                files.append(f)
        files.sort()

        for file_ in files:
            name = file_[:len(file_) - 4]
            text += "\n" + name + " = b'"
            file_encoded = self.encode_base64(file_)
            text += file_encoded.decode('utf-8')
            text += "'\n"

        # Write the generated file
        filename = "base64_sounds.py"
        f = open(filename, 'w', encoding='utf-8-sig')
        f.write(text)
        f.close()
        print("FINISHED CREATING BASE64 SOUNDS HELPER FILE")

    def encode_base64(self, file_path):
        """ """

        with open(file_path, "rb") as image_file:
            base64_string = base64.b64encode(image_file.read())
        return base64_string


if __name__ == '__main__':
    CreateHelperFile()