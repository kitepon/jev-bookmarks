@echo off
rem Chrome Native Messaging host for Windows. Chrome passes the caller origin as arguments.
"%~dp0..\.venv\Scripts\python.exe" -m jev_bookmarks.native_host %*
