from setuptools import setup

setup(name='Katello Certs Tools',
      version='2.8.2',
      description='Python modules used for Katello SSL tooling',
      author='Tomas Lestach',
      author_email='tlestach@redhat.com',
      url='https://github.com/Katello/katello-certs-tools',
      packages=['katello_certs_tools'],
      scripts=['katello-certs-sign', 'katello-certs-gen-rpm'],
      entry_points={
          'console_scripts': [
              'katello-ssl-tool = katello_certs_tools.katello_ssl_tool:main',
          ],
      },
      data_files=[('share/man/man1', ['katello-ssl-tool.1'])])
