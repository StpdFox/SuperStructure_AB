from premise import *
import brightway2 as bw


def build_superstructure_from_premise(self, origin_db, scenarios, db_name, fp):
    exp = export(db=origin_db, filepath=fp)

    # Collect a dictionary of activities
    # {(name, ref_prod, loc, db, unit):row/col index in A matrix}
    rev_ind_A = exp.rev_index(exp.create_names_and_indices_of_A_matrix())

    # Retrieve list of coordinates [activity, activity, value]
    coords_A = exp.create_A_matrix_coordinates()

    # Turn it into a dictionary {(code of receiving activity, code of supplying activity): value}
    original = dict()
    for x in coords_A:
        if (rev_ind_A[x[0]], rev_ind_A[x[1]]) in original:
            original[(rev_ind_A[x[0]], rev_ind_A[x[1]])] += x[2] * -1
        else:
            original[(rev_ind_A[x[0]], rev_ind_A[x[1]])] = x[2] * -1

    # Collect list of substances
    rev_ind_B = exp.rev_index(exp.create_names_and_indices_of_B_matrix())
    # Retrieve list of coordinates of the B matrix [activity index, substance index, value]
    coords_B = exp.create_B_matrix_coordinates()

    # Turn it into a dictionary {(activity name, ref prod, location, database, unit): value}
    original.update({(rev_ind_A[x[0]], rev_ind_B[x[1]]): x[2] * -1 for x in coords_B})

    modified = {}

    print("Looping through scenarios to detect changes...")

    for scenario in scenarios:

        exp = Export(
            db=scenario["database"],
            model=scenario["model"],
            scenario=scenario["pathway"],
            year=scenario["year"],
            filepath=fp,
        )

        new_rev_ind_A = exp.rev_index(exp.create_names_and_indices_of_A_matrix())
        new_coords_A = exp.create_A_matrix_coordinates()

        new = dict()
        for x in new_coords_A:
            if (new_rev_ind_A[x[0]], new_rev_ind_A[x[1]]) in new:
                new[(new_rev_ind_A[x[0]], new_rev_ind_A[x[1]])] += x[2] * -1
            else:
                new[(new_rev_ind_A[x[0]], new_rev_ind_A[x[1]])] = x[2] * -1

        new_coords_B = exp.create_B_matrix_coordinates()
        new.update(
            {(new_rev_ind_A[x[0]], rev_ind_B[x[1]]): x[2] * -1 for x in new_coords_B}
        )
        # List activities that are in the new database but not in the original one
        # As well as exchanges that are present in both databases but with a different value
        list_modified = (i for i in new if i not in original or new[i] != original[i])
        # Also add activities from the original database that are not present in
        # the new one
        list_new = (i for i in original if i not in new)

        list_modified = chain(list_modified, list_new)

        for i in list_modified:
            if i not in modified:
                modified[i] = {"original": original.get(i, 0)}
                modified[i][
                    scenario["model"]
                    + " - "
                    + scenario["pathway"]
                    + " - "
                    + str(scenario["year"])
                    ] = new.get(i, 0)
            else:
                modified[i][
                    scenario["model"]
                    + " - "
                    + scenario["pathway"]
                    + " - "
                    + str(scenario["year"])
                    ] = new.get(i, 0)

    # some scenarios may have not been modified
    # and that means that exchanges might be absent
    # from `modified`
    # so we need to manually add them
    # and set the exchange value similar to that
    # of the original database

    list_scenarios = ["original"] + [s["model"]
                                     + " - "
                                     + s["pathway"]
                                     + " - "
                                     + str(s["year"]) for s in scenarios]

    for m in modified:
        for s in list_scenarios:
            if s not in modified[m].keys():
                # if it is a production exchange
                # the value should be -1
                if m[1] == m[0]:
                    modified[m][s] = -1
                else:
                    modified[m][s] = modified[m]["original"]

    columns = ["from activity name", "from reference product", "from location", "from categories", "from database",
               "from key", "to activity name", "to reference product", "to location", "to categories",
               "to database",
               "to key", "flow type", "original"]
    columns.extend(
        [
            a["model"] + " - " + a["pathway"] + " - " + str(a["year"])
            for a in scenarios
        ]
    )

    print("Export a scenario difference file.")

    l_modified = [columns]

    for m in modified:

        if m[1][2] == "biosphere3":
            d = [
                m[1][0],
                "",
                "",
                m[1][1],
                m[1][2],
                "",
                m[0][0],
                m[0][1],
                m[0][3],
                "",
                db_name,
                "",
                "biosphere"
            ]
        elif (m[1] == m[0] and any(v < 0 for v in modified[m].values())):
            d = [
                m[1][0],
                m[1][1],
                m[1][3],
                "",
                db_name,
                "",
                m[0][0],
                m[0][1],
                m[0][3],
                "",
                db_name,
                "",
                "production"
            ]
        else:
            d = [
                m[1][0],
                m[1][1],
                m[1][3],
                "",
                db_name,
                "",
                m[0][0],
                m[0][1],
                m[0][3],
                "",
                db_name,
                "",
                "technosphere"
            ]

        for s in list_scenarios:
            # we do not want a zero here,
            # as it would render the matrix undetermined
            if m[1] == m[0] and modified[m][s] == 0:
                d.append(1)
            elif m[1] == m[0] and modified[m][s] < 0:
                d.append(modified[m][s] * -1)
            else:
                d.append(modified[m][s])
        l_modified.append(d)

    if fp is not None:
        filepath = Path(fp)
    else:
        filepath = (
                DATA_DIR / "export" / "scenario diff files"
        )

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    filepath = filepath / f"scenario_diff_{date.today()}.xlsx"

    pd.DataFrame(l_modified, columns=[""] * len(columns)).to_excel(
        filepath, index=False
    )

    print(f"Scenario difference file exported to {filepath}!")

    print("Adding extra exchanges to the original database...")

    dict_bio = exp.create_names_and_indices_of_B_matrix()

    for ds in origin_db:
        exc_to_add = []
        for exc in [
            e
            for e in modified
            if e[0]
               == (
                       ds["name"],
                       ds["reference product"],
                       ds["database"],
                       ds["location"],
                       ds["unit"],
               ) and modified[e]["original"] == 0
        ]:
            if isinstance(exc[1][1], tuple):
                exc_to_add.append(
                    {
                        "amount": 0,
                        "input": (
                            "biosphere3",
                            exp.get_bio_code(
                                dict_bio[(exc[1][0], exc[1][1], exc[1][2], exc[1][3])]
                            ),
                        ),
                        "type": "biosphere",
                        "name": exc[1][0],
                        "unit": exc[1][3],
                        "categories": exc[1][1],
                    }
                )

            else:
                exc_to_add.append(
                    {
                        "amount": 0,
                        "type": "technosphere",
                        "product": exc[1][1],
                        "name": exc[1][0],
                        "unit": exc[1][4],
                        "location": exc[1][3],
                    }
                )

        if len(exc_to_add) > 0:
            ds["exchanges"].extend(exc_to_add)

    print("Adding extra activities to the original database...")

    list_act = [
        (a["name"], a["reference product"], a["database"], a["location"], a["unit"])
        for a in origin_db
    ]
    list_to_add = [
        m[0] for m in modified if modified[m]["original"] == 0 and m[0] not in list_act
    ]
    list_to_add = list(set(list_to_add))

    data = []
    for add in list_to_add:
        act_to_add = {
            "location": add[3],
            "name": add[0],
            "reference product": add[1],
            "unit": add[4],
            "database": add[2],
            "code": str(uuid.uuid4().hex),
            "exchanges": [],
        }

        acts = (act for act in modified if act[0] == add)

        for act in acts:
            if isinstance(act[1][1], tuple):
                # this is a biosphere flow
                act_to_add["exchanges"].append(
                    {
                        "uncertainty type": 0,
                        "loc": 0,
                        "amount": 0,
                        "type": "biosphere",
                        "input": (
                            "biosphere3",
                            exp.get_bio_code(
                                dict_bio[(act[1][0], act[1][1], act[1][2], act[1][3])]
                            ),
                        ),
                        "name": act[1][0],
                        "unit": act[1][3],
                        "categories": act[1][1],
                    }
                )

            else:

                if act[1] == act[0]:
                    act_to_add["exchanges"].append(
                        {
                            "uncertainty type": 0,
                            "loc": 1,
                            "amount": 1,
                            "type": "production",
                            "production volume": 0,
                            "product": act[1][1],
                            "name": act[1][0],
                            "unit": act[1][4],
                            "location": act[1][3],
                        }
                    )

                else:

                    act_to_add["exchanges"].append(
                        {
                            "uncertainty type": 0,
                            "loc": 0,
                            "amount": 0,
                            "type": "technosphere",
                            "production volume": 0,
                            "product": act[1][1],
                            "name": act[1][0],
                            "unit": act[1][4],
                            "location": act[1][3],
                        }
                    )
        data.append(act_to_add)
    origin_db.extend(data)

    return origin_db
#list the projects in BW
bw.projects


