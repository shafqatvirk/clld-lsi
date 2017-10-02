from setuptools import setup, find_packages


requires = [
    'clld',
]

setup(
    name='lsi',
    version='0.0',
    description='lsi',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=['mock==1.0'],
    test_suite="lsi",
    entry_points="""\
    [paste.app_factory]
    main = lsi:main
    """)
