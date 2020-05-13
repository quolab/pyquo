from setuptools import setup
import pathlib

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(name='pyquo',
      version='20.1.1',
      description='Python QuoLab REST Client',
      long_description=README,
      long_description_content_type='text/markdown',
      author='QuoLab Technologies',
      author_email='curious@quolab.com',
      packages=['pyquo'],
      url='https://github.com/quolab/pyquo',
      install_requires=[
          'certifi==2018.8.24',
          'chardet==3.0.4',
          'idna==2.6',
          'requests==2.21.0',
          'six==1.12.0',
          'urllib3==1.24.1'
      ])
