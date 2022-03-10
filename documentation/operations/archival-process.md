# Archival Process

To archive the instances you will need to connect to the Ocim server using ssh and use the Django shell to archive instances since there is currently no UI to do so. Please, don't wait for the archival process for more than 5 minutes once it's running; this takes some hours to run, so it's better to check back later.

*  Connect to Ocim using: `ssh ocim@ocim.example.com`.
*  See a list of screens with `screen -list`.
*  The one that ends with "ocim" is what we want: `screen -r .ocim` (or similar Ocim screen name).
*  There are multiple screen windows in that session including one that runs the Ocim app in the foreground. Be careful not to fiddle with it or kill it by accident.
*  You can switch around windows in screen with CTRL+a followed by SHIFT+" (press control and 'a' together, then shift and the double-quote key).
*  Select one until you find one where you're logged in as `www-data` in the `~/opencraft` folder with the `opencraft` venv activated.
*  Run the following command to archive the instances: `make manage 'archive_instances --domains=sandbox.example.com,test.example.com'`.
*  You can detach from the screen session with CTRL+a followed by d (control and 'a' together, then 'd').

**Helpful Links**

[GNU Screen Cheat Sheet](https://gist.github.com/fredrick/1216878)
