os-trello: OpenStack Tooling -> Trello Sync
===========================================

os-trello syncs reviews from Gerrit and bugs from Launchpad to Trello. This
gives the OpenStack developer a single place to look for what tasks they
should be working on.

os-trello, by default, will pull in any Gerrit review that you have starred
or any review that you have published. This is configurable from within the
configuration file.

os-trello will also pull in Launchpad bugs that you are subscribed to or that
are assigned to you. This is not configurable and will likely change as I
discover what this tool will do to my workflow.

Checkout the `public Trello board <https://trello.com/b/kAcLdBiq/openstack>`_
I use for OpenStack development.

Workflow
--------

I've only been using this tool for about a week so the workflow described
below is likely to change. If there is a demand for it, I would consider
making it as configurable as possible so that not everyone has to have the
same workflow.

As a general principle cards are moved through the lists automatically. The
only exception is that I manually move them into 'In Progress' when I start
working on them. Cards in 'In Progress' are not automatically moved into
'Needs Work', but will be moved into the other lists as needed.

Reviews
~~~~~~~

1. Reviews that are not mine

   a. If I need to review them they are in the 'Needs Work' list
   b. If I have reviewed the current version already it will be in the
      'Completed' list
   c. If the review has a +A and is not yet merged it will be in the
      'Gating' list
   d. If the review has merged or was abandoned it will be in the 'Done' list

2. Reviews that are mine currently follow the same workflow, but that will
   change soon to be smarter.

Bugs
~~~~

All bugs currently follow the same generic workflow.

1. A bug with a status of 'Fix Committed' or 'Fix Released' will be in the
   'Done' list
2. A bug with a status of 'New', 'Confirmed', 'Triaged' or 'In Progress' will
   be in the 'Needs Work' list

I think the goal will be to figure out when I need to go back and comment.
The rules here are not as clear to me.

Ordering
~~~~~~~~

Right now the reviews get loaded first and the bugs second. There is no
automatic ordering. You are free to reorder based on your priorites and
that order will be maintained.

Getting Started
---------------

These instructions assume that you already have os-trello installed.

1. Go create a new Trello board (I named mine 'OpenStack')
2. Create the ~/.config/os-trello directory
3. Copy the example config `os-trello.example.yaml` to
   `~/.config/os-trello/os-trello.yaml`
4. Edit the config

   a. Set the Trello key (can be found here: https://trello.com/app-key)
   b. Set the Trello board_id to the short code found in the address bar of
      your browser when you are viewing your board (mine from the link above
      is 'kAcLdBiq')
   c. Set your gerrit username/password (they can be found here:
      https://review.openstack.org/#/settings/http-password)
   d. Set your launchpad username

5. Run `os-trello-init` and follow the instructions for authorizing the
   application with Trello
6. Set the Trello token to the value you received in the previous step
7. Run `os-trello-init` again to actually setup the Trello board
8. Run `os-trello-sync` to sync

I run `os-trello-sync` in a cron that runs once an hour.
