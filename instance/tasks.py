from huey.djhuey import task

@task()
def count_beans(number):
    print('-- counted {} beans --'.format(number))
    return 'Counted {} beans'.format(number)

