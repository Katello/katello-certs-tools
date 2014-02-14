from distutils.core import setup

setup(name='Katello Certs Tools',
      version='1.5.1',
      description='Python modules used for Katello SSL tooling',
      author='Tomas Lestach',
      author_email='tlestach@redhat.com',
      url='https://fedorahosted.org/katello/',
      packages=['katello_certs_tools'],
      scripts=['katello-ssl-tool', 'katello-sudo-ssl-tool', 'katello-certs-sign', 'katello-certs-gen-rpm'],
      data_files=[('share/man/man1', ['katello-ssl-tool.1'])]
)
