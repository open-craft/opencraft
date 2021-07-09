# Continuous Integration

This describes aspects of Continuous Integration setup specifically for OpenCraft,
and is of limited interest for external contributors.

## Cleaning up left-over resources

Test runs (especially failing ones) may occasionally leave behind resources that,
over time, clutter the underlying infrastructure.

To avoid this, there is [a `scheduled-cleanup` CircleCI workflow](https://github.com/open-craft/opencraft/blob/master/circle.yml)
that regularly runs the `cleanup` job.

If necessary (usually when testing changes to it), the job may be run on-demand
by pushing to the `ci-cleanup` branch.
