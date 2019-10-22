# ulauncher-notes-nv

A [NotationalVelocity](http://notational.net/)-inspired [Ulauncher](https://ulauncher.io/) extension for storing and retrieving notes as individual text files.

## Features

- Keyboard-centric search-first user experience: every action, including new note creation, begins with a search
- Intuitive fuzzy search of note titles and contents in Ulauncher
- Notes are stored as individual text/markdown/whatever files in a directory
- Use your whatever editor you like to view and edit notes


## Why?

NotationalVelocity is a Mac OS application with a cult following. In its own words:

> NOTATIONAL VELOCITY is an application that stores and retrieves notes.

> It is an attempt to loosen the mental blockages to recording information and to scrape away the tartar of convention that handicaps its retrieval. The solution is by nature nonconformist.

The "nonconformist" part is NV ditching the traditional file-oriented actions of "create", "open" etc to reduce the number of steps required to store or access a piece of content:

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
- `Command to open note`: command to be executed to open the selected note file. Use the `%p` token to insert the full path to the note file. (If left empty, default application associated with that file type will be executed via `xdg-open`, e.g. default for `.txt` in Ubuntu is `Gedit`)

## Usage

Open Ulauncher and type in "nv " to start the extension. If everything is configured correctly, you'll see a partial list of your notes files, most recently accessed or modified first:

![All notes, no query](images/screenshots/empty-query.png)

Start typing the search query and the list if filtered down accordingly:

![Query 1](images/screenshots/search-query-1.png)

The more concrete the search, the smaller the resulting list:

![Query 2](images/screenshots/search-query-2.png)

## Troubleshooting

### Why doesn't my editor application window come to the foreground after I open the note?

...wmctrl something?...

## Inspiration and thanks

I loved NotationalVelocity and its modern fork [NVAlt](https://brettterpstra.com/projects/nvalt/) on MacOS, and I've been searching for a replacement ever since switching to Linux.
