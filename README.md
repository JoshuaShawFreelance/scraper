- [Installing Python and pipenv](https://github.com/LambdaSchool/CS-Wiki/wiki/Installing-Python-3-and-pipenv)
- [JavaScript<->Python cheatsheet](https://github.com/LambdaSchool/CS-Wiki/wiki/Javascript-Python-cheatsheet)
- [How to read Specs and Code](https://github.com/LambdaSchool/CS-Wiki/wiki/How-to-Read-Specifications-and-Code)
- [Python 3 standard library](https://docs.python.org/3.6/library/)

## Getting started

1. Make sure you have Python 3 and pipenv installed (Homebrew is a good option on macOS)

   ```
   brew install python pipenv
   ```

2. Go to the directory with the `Pipfile` and run

   ```
   pipenv install
   ```

3. After the install completes, run

   ```
   pipenv shell
   ```

   This will get you into the virtual environment. At this point, you should be
   able to run Python 3 by just running `python`:

   ```
   $ python --version
   Python 3.8.5
   ```

4. Run the program

   ```
   python main.py
   ```

   It should write to a `db.json` file in the root folder. There you can inspect what it scraped.

   You can exit the virtual environment by typing `exit`.
