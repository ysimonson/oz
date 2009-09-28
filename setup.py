from distutils.core import setup

setup(name = 'Oz',
      version = '0.2',
      description = 'A set of tools for the Tornado web framework',
      author = 'Yusuf Simonson',
      url = 'http://github.com/ysimonson/oz',
      packages = ['oz',],
      data_files = [
          ('', ['README', 'LICENSE']),
          ('oz', ['oz/error_template.html']),
      ]
     )