from myconn import Database
# Read a formula from DB


def read_formula(comPk):

    query = """	SELECT
                                    `F`.*,
                                    `FC`.*
                                FROM
                                    `tblCompetition` `C`
                                    JOIN `tblForComp` `FC` USING (`comPk`)
                                    LEFT OUTER JOIN `tblFormula` `F` USING (`forPk`)
                                WHERE
                                    `C`.`comPk` = %s """
    with Database() as db:
        # get the formula details.
        formula = db.fetchone(query, [comPk])
    formula['forMinDistance'] *= 1000
    formula['forNomDistance'] *= 1000
    formula['forNomTime'] *= 60
    formula['forDiffDist'] *= 1000
#    formula['ScaleToValidity'] = formula['forScaleToValidity']
    # FIX: add failsafe checking?
    if formula['forMinDistance'] <= 0:

        print("WARNING: mindist <= 0, using 5000m instead")
        formula['forMinDistance'] = 5000

    return formula
