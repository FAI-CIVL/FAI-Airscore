#!/bin/sh

#
# Quickie script to centralise the mysql password setting
#

#all=`grep -l MYSQLPASSWORD *.pm *.pl *.php *.sql`

# Check we have the macro (at least)
macro=$1
if [ z$macro = z ];
then
    echo "$0 <macro> <string>";
    exit 1
fi

# Restore originals
all=`ls *.b4sub`
for i in $all
do
    orig=`echo $i | cut -d. -f1-2`
    cp $i $orig 
done

# If we have a string for substitution
if [ z$2 != z ];
then
    all=`grep -l $macro *.pm *.pl *.php *.sql`
    # Substitute
    for i in $all
    do
        echo $i
        cp $i $i.b4sub
        sed -e "s+%$macro%+$2+" $i > $i.sub
        mv $i.sub $i
    done
fi


