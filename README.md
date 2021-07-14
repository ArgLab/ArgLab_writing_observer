# Writing Observer and Learning Observer

![Writing Observer Logo](learning_observer/learning_observer/static/media/logo-clean.jpg)

This repository is part of a project to provide an open source
learning analytics dashboard to help instructors be able to manage
student learning processes, and in particular, student writing
processes.

## Learning Observer

Learning Observer is designed as an open source, open science learning
process data dashboarding framework. You write reducers to handle
per-student writing data, and aggegators to make dashboards. We've
tested this in math and writing, but our focus is on writing process
data.

It's not finished, but it's moving along quickly.

## Writing Observer

Writing Observer is a plug-in for Google Docs which visualizes writing
data to teachers. Our immediate goal was to provide a dashboard which
gives rapid, actionable insights to educators supporting remote
learning during this pandemic. We're working to expand this to support
a broad range of write-to-learn and collaborative learning techniques.

## Status

There isn't much to see here for external collaborators yet. This
repository has a series of prototypes to confirm we can:

* collect the data we want;
* extract what we need from it; and
* route it to where we want it to go (there's *a lot* of data, with
  complex dependencies, so this is actually a nontrivial problem)

Which mitigates most of the technical risk. We also now integrate with
Google Classroom. We also have prototype APIs for making dashboards, and
a few prototype dashboards.

For this to be useful, we'll need to provide some basic documentation
for developers to be able to navigate this repo (in particular,
explaining *why* this approach works).

This system is designed to be *massively* scalable, but it is not
currently implemented to be so. It would take work to flush out all of
the performance issues. We'd like to do that work once we better
understand what we're doing.

Getting Started
===============

As an early prototype, getting started isn't seamless. Run:

~~~~~
make install
~~~~~

And follow the instructions. Then fix up the makefile and make a PR :)

Once that's done, run:

~~~~
make
~~~~

Again, fix up the makefile, and make a PR.


To setup writing_observer on top of the learning observer platform you must go into modules/writing_observer and run:

   sudo python setup.py develop


Additional System-Specific Notes
-----------------------------------

RHEL systems require the addition of the rh-python38 packages.
You also must also install the separate devel packages.  

The virtualenv once created on RHEL will be stored in your home directory under .virtualenvs.



Contact/maintainer: Piotr Mitros (pmitros@ets.org)

Licensing: Open source / free software. License TBD. 


