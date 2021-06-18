# Management Tasks

This describes the tasks available for managing the OCIM related infrastructure.
These are launched as regular Django Management Tasks:
```sh
./manage.py TASK_NAME
```

For help with any command:
```sh
./manage TASK_NAME -h
```

## `find_orphan_dbs`

This task finds orphaned databases, i.e., databases that
still exist on their hosts but are not registered in OCIM,
which may happen when there is a failure in deprovisioning
those databases.

### Example

```sh
# 1> is stdout
# 2> is stderr
root@a96391daf5b5:/usr/src/ocim#./manage.py find_orphan_dbs mongo --exclude-dbs my_real_db
2> Finding orphaned MongoDB databases...
2> Looking in mongo.example.com
1> mongo    mongo.example.com:27017 test
2> 1 orphaned MongoDB databases were found on mongo:27017.
```