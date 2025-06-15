# Contributing Guidelines
*All pull requests, bug reports, feature requests, and other forms of contribution are welcome!* :blue_heart:

#### Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Issue Tracking](#issue-tracking)
- [Security Issues](#security-issues)
- [Feature Requests](#feature-requests)
- [Roadmap](#roadmap)
- [Pull Requests](#pull-requests)
- [Code Style](#code-style)
- [Code Review](#code-review)
- [Templates](#templates)

## Code of Conduct
The entire [Code of Conduct](https://github.com/thpsrun/website/.github/blog/main/CODE_OF_CONDUCT.md) is available for you to read. Essentially, don't be an idiot; this is an inclusive project. If you disagree, just go away.

## Issue Tracking
Before you [create an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue), please check to make sure you are on the latest version of this project. If you are not on it, upgrade to the current `main` branch to see if it fixes your issues. If not, feel free to submit an issue!

This also includes bug reports and smaller issues; feel free to submit them for review. However, please provide as much information as possible (screenshots help too).

## Security Issues
Please review the [Security Policy](https://github.com/thpsrun/website/.github/blog/main/SECURITY.md) if you have any security or vulnerability concerns. Do __**NOT**__ submit a public issue with vulnerabilities, please!

## Feature Requests
Feature requests are most definitely welcome! All of these will be reviewed to see what can be added to the project and determine what could be eventually added to the roadmap. Again, give plenty of information about your suggestion! Just a single sentence like "pls add blah" may not suffice.

## Roadmap
Speaking of a roadmap, be sure to check the Projects section to see what is coming up in later iterations of this website!

## Pull Requests
If you are interested in assiting with the project, pull requests are a wonderful way to do it! Feel free to fork the repository and create a pull request if you wish to contribute.

For larger changes, please open an issue first so we can discuss the plan. Communication is key! Additionally, we ask you follow these rules:

-   **Readability**: Your code should be legible and understood. If a code block cannot be easily understood or explained, either refactor it OR add comments.
-   **Documentation**: Larger changes should be better documented. This includes docstrings, in-line comments, multi-line comments, and so on. Again, communication is key!
-   **Python Code Style**: While we are not sticklers on code formatting, you are expected to adhere to style guidelines, formatting, and to give a solid pass to ensure your code adheres to PEP8. There are style guide violations that are ignored; the most up-to-date will be `.flake8` file in the main branch. With that in mind, flake8 is the preferred styler; but feel free to use your own!
-   **Update CHANGELOG.md**: Try to follow the formatting examples throughout the document, and feel free to add some humor to it as well! Be sure to add a comment at the end of the change that includes your username and link to your GitHub so you are credited!
-   **Main Branch**: Always fork and branch from the `main` branch to stay up-to-date.
-   **Commit Messages**: Write a superb commit message! A good commit message summarizes what you did in the subject line, and goes over why the commit is needed. Add additional information, issue numbers, and so on as needed.

## Code Style
I (ThePackle) am not a stickler about coding standards, but it should definitely be legible, understandable, and not be overly complex. Here are the rules I stick to:
-   **PEP8**: Again, not a stickler, but I have done a lot to follow the PEP8 (Python Code Style) standard. It isn't a requirement to follow every rule to the T, but you are expected to follow a large majority of the rules. Specific rules ignored are listed in the `.flake8` file in the main branch.
-   **Line Length**: 100. No more than that (unless you have an incredibly valid reason).
-   **Inline Statements**: Inline statements (if/elif/else, while, etc) are all acceptable to be on a single line **IF** they are under 100 characters *AND* it is legible. Clarity is important!
-   **Breaking Up Code**: Utilize parentheses, especially when dealing with models, querysets, and filters. You can easily take something like:
```test_variable = MyLongModel.objects.only("id, "title", "name", "game", "player", "player2", "level").filter(id__iexact="blah", player_name__iexact="ThePackle")```
and transform it into:
```
test_variable = (
    MyLongModel.objects
    .only("id, "title", "name", "game", "player", "player2", "level")
    .filter(id__iexact="blah", player_name__iexact="ThePackle")
)
```
If something like the `.only` or `.filter` methods are taking up a lot of characters, you can also start a new line from there!
```
test_variable = (
    MyLongModel.objects
    .only(
        "id, "title", "name", "game", "player", "player2", "level"
    )
    .filter(
        id__iexact="blah", player_name__iexact="ThePackle"
    )
)
```
Just make sure you make sure that the parentheses line up! You do not need to go overboard and have it broken up like the last example, but try your best to make it make sense too!
-   **Breaking Up Arguments**: Similar to the last rule, here is a snippet from `/srl/tasks.py`:
```
def add_run(
    game, run, category, level, run_variables, obsolete=False, point_reset=True, download_pfp=True
):
```
This is totally fine and stays under the 100 character limit. However, two rules:
    1.  If you have a lot of arguments, feel free to make another line to break them up further. You do not need to separate each argument into its own line.
    2.  The ONLY time you would break up the arguments into their own lines is if the argument names are obnoxiously long (e.g., `this_is_my_super_long_argument_i_have_no_clue_why_its_this_long_aaaaaa`).
-   **Docstrings**: All classes, methods, and functions within this project are expected to have either one-line docstring or full-length docstring.
    -   One-line docstrings should be added EVEN if it is obvious.
    -   Multi-line docstrings should include as much information as possible, to include (but not limited to):
        -   Arguments
        -   Methods
        -   Returns
        -   Raises
        -   Calls (nested or called functions within a function)
        -   Whatever else you think is best!
    
    Obviously, I am not super picky about how docstrings should be formatted. But, they SHOULD explain what you are doing very well!
-   **TitleCase vs snake_case**: TitleCase (e.g., MyFunction or MySuperFunction) should be used for classes and models. snake_case should be used for functions, variables, and arguments.
-   **Comments!!**: As someone who is incredibly bad about commenting his code and is trying to be better, I urge you to do the same! If the code talks for itself, cool! If it makes some sense or is kind of confusing, a few comment lines won't hurt!
-   **Flake8**: As mentioned with the `.flake8` file, Flake8 is what was used for styling. If you wish to use something else like ruff, feel free! Just make sure to exclude the violations mentioned in that file! :smile:

## Code Review
-   **Review the code, not the author.** Look for and suggest improvements without disparaging or insulting the author. Provide actionable feedback and explain your reasoning.
-   **You are not your code.** When your code is critiqued, questioned, or constructively criticized, remember that you are not your code. Do not take code review personally.
-   **Always do your best.** No one writes bugs on purpose. Do your best, and learn from your mistakes.
-   Kindly note any violations to the guidelines specified in this document. 

## Templates
Templates will be added over time, depending on volume of project. If you want to contribute a template or idea, feel free to submit a PR with your ideas!