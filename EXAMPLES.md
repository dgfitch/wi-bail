Once you have inmate data loaded (see [README](README.md),
you can run

    poetry run bail query

And then do various queries like:

    statuses = set(select(i.status for i in Inmate))
    pretrial = set(s for s in statuses if ("Prearraignment" in s or "Pretrial" in s))

    pretrial_inmates = list(select(i for i in Inmate if i.status in pretrial))
    other_inmates = list(select(i for i in Inmate if not i.status in pretrial))

    black_pretrial_inmates = list(select(i for i in Inmate if i.race == "African American" and i.status in pretrial))
    other_pretrial_inmates = list(select(i for i in Inmate if i.race != "African American" and i.status in pretrial))

    len(pretrial_inmates)
    # 243

    len(other_inmates)
    # 363

    len(black_pretrial_inmates)
    # 138

    # Now the booking dates are strings, let's make a function that can return 
    # how long they've been in jail
