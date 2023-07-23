from tinytag import TinyTag
from pathvalidate import sanitize_filename as clean
from glob import glob
import shutil
import fire
import sys
import os
import json

from ruamel.yaml import YAML

from pathlib import Path

from .dotconfig import Config

yaml = YAML(typ='safe')
yaml.default_flow_style = False

SERIES_SPLIT = [
    ', Book ',
    ' Series #',
]

class ABMgr():
    """Audo Book Manager"""
    def __init__(self):
        self.__app_config = Config('abmgr', 'settings', defaults={})

        if 'paths' not in self.__app_config:
            print('No previous configuration found. Please setup.')
            self.setup()
            sys.exit(0)
        
    def setup(self):
        """Run initial config setup"""
        paths = {}
        p = input('OpenAudible Library Path: ')
        
        if not Path(p).exists():
            print(f'Directory does not exist {p}')
            sys.exit(1)
        paths['oa_lib_dir'] = str(Path(p).absolute().as_posix())
        
        p = input('ABS Output Path: ')
        if not Path(p).exists():
            print(f'Directory does not exist {p}')
            sys.exit(1)
        paths['abs_lib_dir'] = str(Path(p).absolute().as_posix())
        
        self.__app_config['paths'] = paths
        self.__app_config.write()
        
        save_path = Path(self.__app_config.full_path).absolute().as_posix()
        print(f'\nBase configuration saved to: {save_path}')
    
    def __get_oa_books(self, oa_lib_dir):
        books_path = oa_lib_dir / 'books'
        
        results = []
        
        #print('Scanning books...\n')
        
        for b in books_path.iterdir():
            if b.suffix.lower() == '.m4b':
                meta = TinyTag.get(str(b.resolve()))
                short_title = str(meta.album)
                author = str(meta.artist)
                long_title = str(meta.title)
                series = None
                book_num = None
                
                if long_title != short_title:
                    series = long_title[(len(short_title) + 3):]

                    if series.endswith(')'):
                        start = series.find('(')
                        series = series[start+1:-1]
                        
                    if series.startswith('Book '):
                        book_num = series[5:]
                        series = short_title
                    else:
                        for split in SERIES_SPLIT:
                            if split in series:
                                series, book_num = series.split(split)
                            
                book = {
                    'path': str(b.as_posix()),
                    'author': author,
                    'title': long_title,
                    'short_title': short_title,
                    'series': series,
                    'book_num': book_num
                }

                results.append(book)

        return results
        
    def sync(self):
        """Read books from OpenAudible"""
        paths = self.__app_config['paths']
        oa_lib_dir = Path(paths['oa_lib_dir'])
        abs_lib_dir = Path(paths['abs_lib_dir'])
        books_path = oa_lib_dir / 'books'
        
        # books = self.__get_oa_books(oa_lib_dir)
        books = self.__read_oa_library(oa_lib_dir)

        print('Copying to output...')
        
        #Author(s) Name\Series Name\Book # - Book Title\Audiofiles
        for b in books:
            src_path =      b['path']
            filename =      b['filename']
            author =        b['author']
            title =         b['title']
            short_title =   b['short_title']
            series =        b['series']
            book_num =      b['book_num']            
            
            save_path = abs_lib_dir / author
            
            if series is not None:
                if book_num is not None:
                    book_title = f'{book_num} - {short_title}'
                else:
                    book_title = short_title
                save_path = save_path / clean(series) / clean(book_title)
            else:
                save_path = save_path / clean(title)
                
            print(f'{src_path} -->\n{save_path.as_posix()}/{filename}\n')
            
            if not save_path.exists():
                # print(f'mkdir {save_path}')
                save_path.mkdir(parents=True, exist_ok=True)
                
            m4b_path = save_path / filename
            if(not m4b_path.exists()):
                Path(src_path).link_to(m4b_path)
                #m4b_path.hardlink_to(src_path) #python 3.10 version
                
            
    
    def __read_oa_library(self, oa_lib_dir):
        books_lib = oa_lib_dir / 'books.json'
        books_dir = oa_lib_dir / 'books'
        
        results = []
        
        print('Scanning books...\n')
        
        with open(books_lib, encoding='utf-8', mode='r') as f:
            books_data = json.load(f)
            
        for b in books_data:
            filename = b['filename'] + '.m4b'
            book = {
                'path': f'{books_dir}/{filename}',
                'filename': filename,
                'author': b['author'],
                'title': b['title'],
                'short_title': b['title_short'],
                'narrated_by': b.get('narrated_by', None),
                'series': b.get('series_name', None),
                'book_num': b.get('series_sequence', None),
            }
            results.append(book)
            
        return results
    
    def read(self):
        paths = self.__app_config['paths']
        oa_lib_dir = Path(paths['oa_lib_dir'])
        abs_lib_dir = Path(paths['abs_lib_dir'])
        books_path = oa_lib_dir / 'books'
        
        books = self.__read_oa_library(oa_lib_dir)
        
        print(json.dumps(books, indent=2))
        
def main():
    fire.Fire(ABMgr)

# out_path = Path('S:\Data\AudioBooks\Audible')
# # out_path = Path('B:\Audible')
# base_path = Path(__file__).parent.absolute()
# books_path = Path(base_path) / 'books'

# for b in books_path.iterdir():
#     if b.suffix.lower() == '.m4b':
#         meta = TinyTag.get(str(b.resolve()))
#         artist = clean(meta.artist)
#         save_path = out_path / artist
#         if not save_path.exists():
#             print(f'mkdir {save_path}')
#             save_path.mkdir(parents=True, exist_ok=True)
            
#         new_file = save_path / b.name
#         if new_file.exists():
#             print(f'<< Skip: {new_file}')
#         else:
#             print(f'>> Copy: {new_file}')
#             shutil.copy(b, new_file)

