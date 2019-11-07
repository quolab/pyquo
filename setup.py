from distutils.core import setup

setup(name='pyquo',
      version='19.0.11',
      description='Python quolab rest client',
      author='Joel Thomas',
      author_email='joel.thomas@quocsient.io',
      packages=['pyquo'],
      install_requires=[
          'certifi==2017.11.5',
          'chardet==3.0.4',
          'idna==2.6',
          'requests==2.18.4',
          'six==1.11.0',
          'urllib3==1.22'
      ])
