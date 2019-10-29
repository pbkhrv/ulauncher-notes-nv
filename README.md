# ulauncher-notes-nv

A [NotationalVelocity](http://notational.net/)-inspired [Ulauncher](https://ulauncher.io/) extension for storing and retrieving notes as individual text files.


## Features

- Keyboard-centric search-first user experience: every action, including new note creation, begins with a search
- Intuitive fuzzy search of note titles and contents in Ulauncher
- Notes are stored as individual text/markdown/whatever files in a directory - use your favorite tools to keep notes synchronized across devices
- Use your favorite editor you like to view and edit notes


## Why?

NotationalVelocity is a Mac OS application with a cult following. [In its own words](http://notational.net):

> NOTATIONAL VELOCITY is an application that stores and retrieves notes.

> It is an attempt to loosen the mental blockages to recording information and to scrape away the tartar of convention that handicaps its retrieval. The solution is by nature nonconformist.

The "nonconformist" part is the one where NV ditched the traditional file-oriented actions of "create", "open" etc to reduce the number of steps required to store or access a piece of textual content:

> Searching for notes is not a separate action; rather, it is the primary interface.

> Searching encompasses all notes' content and occurs instantly with each key pressed.

> Notational Velocity's window was designed for keyboard input above all else, and thus has no buttons.

Ulauncher happens to share the search-centric design goals. The only thing it doesn't provide is a text editor, and the hope is that using an external editor won't detract from the overall user experience too much.


## Installation

Open Ulauncher preferences window -> Extensions -> "Add extension" and paste the following url:

```
https://github.com/pbkhrv/ulauncher-notes-nv
```


## Configuration

- `Notes directory path`: path to where your notes files are stored.
- `Command to open note`: command to be executed to open the selected note file. Use the `{fn}` field to insert the full path to the note file. (If left empty, default application associated with that file type will be executed via `xdg-open`, e.g. default for `.txt` in Ubuntu is `gedit`)


## Usage

Open Ulauncher and type in "nv " to start the extension. If everything is configured correctly, you'll see a partial list of your notes files, most recently modified on top:

![All notes, no query](images/screenshots/empty-query.png)

Start typing a search query to get instant results. Select an note and press Enter to open it in the text editor that you configured in Preferences:

![Query 1](images/screenshots/search-query1.png)

The more concrete the search, the smaller the resulting list:

![Query 2](images/screenshots/search-query2.png)

You can also use the search query as a title of a new note. Press Enter to create and open the new note:

![Create note](images/screenshots/create-note.png)


## Inspiration and thanks

I loved NotationalVelocity and its modern fork [NVAlt](https://brettterpstra.com/projects/nvalt/) on Mac OS, and I've been (largely unsuccessfully) searching for something as good on Linux for a while.