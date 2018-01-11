# -*- coding: utf-8 -*-
# import section
from __future__ import absolute_import, unicode_literals
from steganography.steganography import Steganography
# from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex, b2a_base64, a2b_base64
import sys
import os
import argparse
import time
import requests
# import ctypes
import StringIO
import requests
import shutil
from os import path, access, R_OK  # W_OK for write permission.
# from mechanize import Browser, Link, LWPCookieJar
import re
# from PIL import Image
# from selenium import webdriver
# from selenium.webdriver import ActionChains
# from selenium.webdriver.common.keys import Keys
from difflib import unified_diff
# from git import *
# from githubInterface import GithubGitFileManager, GithubFileManager
# from scrapy.spider import BaseSpider
# from bs4 import BeautifulSou


def str2bool(v):
    return str(v).lower() in ("yes", "true", "t", "y", "1")


def stegano_image(ifile_name, ofile_name, text):
    Steganography.encode(ifile_name, ofile_name, text)
    return


def destegano_image(file_name):
    # read secret text from image
    secret_text = Steganography.decode(file_name)
    return secret_text


def convert_binary_to_text(data):
    text = b2a_base64(data)
    return text


def convert_text_to_binary(text):
    data = a2b_base64(text)
    return data



##################################
#   Main:
##################################
def main() :
    parser = argparse.ArgumentParser(description = 'Utility to stegano file online')
    parser.add_argument('-p', '--post', dest='post_to_cloud', default=False,
                        help='Stegano ifile and post it to cloud. Default is False.')
    parser.add_argument('-f', '--fetch', dest='fetch_from_cloud', default=False,
                        help='Fetch data from cloud, destegano it and store it as ofile locally.Default is False.')
    parser.add_argument('-if', '--input_filename', dest='input_file', default=None,
                        help='File path name to the FILE which should be steganoed and stored.')
    parser.add_argument('-i', '--image_filename', dest='image_filename', default=None,
                        help='File path name to the IMAGE which should be base of stegano and stored.')
    parser.add_argument('-of', '--output_filename', dest='output_file', default=None,
                        help='File path name to the FILE which should be fetched online and desteganoed locally.')

    # To-Do: need some codes to try and catch exceptions.
    args = parser.parse_args()
    post_to_cloud = str2bool(vars(args)['post_to_cloud'])
    fetch_from_cloud = str2bool(vars(args)['fetch_from_cloud'])
    input_file = vars(args)['input_file']
    output_file = vars(args)['output_file']
    image_filename = vars(args)['image_filename']
    verbose_mode = True

    ret = 0
    if post_to_cloud is True:
        if input_file is None:
            print "Please provide input file name with -if when post something to cloud."
            ret = -1
        elif image_filename is None:
            print "Please provide image file name with -i when post something to cloud."
            ret = -1
        else:
            # todo: check whether input_file & image is readable
            # if path.exists(today_html_name) and path.isfile(today_html_name) and access(today_html_name, R_OK)
            # todo: better to zip ifile before base64 it
            with open(input_file, 'rb') as ifile:
                data = ifile.read()
                print "Successfully read input file as ", input_file

            text = convert_binary_to_text(data)
            print "Successfully convert data to text."

            print "Starting stega image ", image_filename
            tempfile_name = os.path.join(os.path.dirname(input_file), 'tmp.tmp')
            stegano_image(image_filename, tempfile_name, text)
            print "Successfully stega image and output as ", tempfile_name

            # todo: send this file to cloud
            print "Successfully stegano a file as image ", tempfile_name

    if fetch_from_cloud is True:
        if output_file is None:
            print "Please provide output file name with -of when fetch something from cloud & store locally."
            return -1
        else:
            # todo: fetch image from cloud
            # todo: remove this image_filename here, we use it as tricky workaround

            print "Starting destega imagefile ", image_filename
            text = destegano_image(image_filename)
            print "Successfully destega image."

            data = convert_text_to_binary(text)
            print "Successfully convert text to data."

            with open(output_file, 'wb') as ofile:
                ofile.write(data)
            print "Successfully destegano a file as %s", output_file

    return ret


if __name__ == '__main__':
    ret = main()
    exit(ret)

