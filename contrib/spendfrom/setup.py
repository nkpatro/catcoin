from distutils.core import setup
setup(name='btcspendfrom',
      version='1.0',
      description='Command-line utility for fieldcoin "coin control"',
      author='Gavin Andresen',
      author_email='gavin@fieldcoinfoundation.org',
      requires=['jsonrpc'],
      scripts=['spendfrom.py'],
      )
