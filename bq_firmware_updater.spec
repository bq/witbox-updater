# -*- mode: python -*-

block_cipher = None

files_to_add = [('./images/*', 'images/'),
                ('./utils/avrdude.exe', 'utils/'),
                ('./utils/avrdude.conf', 'utils/'),
                ('./utils/libusb0.dll', 'utils/')]

a = Analysis(['bq_firmware_updater.py'],
             pathex=['C:\\Users\\startic1\\Documents\\bqFirmwareUpdater'],
             binaries=None,
             datas=files_to_add,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='BQ_Firmware_Updater',
          debug=False,
          strip=False,
          upx=True,
          console=False,
          icon="images\\32.ico" )
