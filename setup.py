from setuptools import setup
import os, subprocess

with open('README.org', 'r') as f:
    long_description = f.read()


setup(
    name = 'nedr',
    version = '0.1',
    author = 'Dou Meishi',
    author_email = 'doumeishi@qq.com',
    description = 'Numerical Experiment Data Recorder',
    long_description = long_description,
    url = "https://github.com/Dou-Meishi/nedr",
    packages = ['nedr'],
    python_requires='>=3.6'
)


# copy executable script
src = './nedr/bin/nedr'
dst = os.path.expanduser('~/bin/')

if not os.path.exists(dst):
    os.mkdir(dst)

subprocess.run(['cp', '-f', src, dst])
subprocess.run(['chmod', 'a+x', dst+'nedr'])
