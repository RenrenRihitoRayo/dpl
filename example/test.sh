mkdir "errors" &> /dev/null

failed_test=()
fails=0

for file in *; do
	if [ "$file" = "00-class.dpl" ]; then
		continue
	fi
	if [ "${file%%-*}" = "xx" ]; then
		continue
	fi
	if [ -f "$file" ]; then
		if [ "${file##*.}" != "dpl" ]; then
			continue	
		fi
		python3 ../dpl.py -simple-run -no-lupa -no-cffi $file &> temp.txt 
		if [ "$?" -ne "0" ]; then
			echo "$file: Failed [$?]"
			cp temp.txt "./errors/${file}.err"
			fails=$((fails + 1))
			failed_test+=($file)
			continue
		fi
		echo "$file: Passed"
	fi
done

if [ $fails -ne 0 ]; then
	echo -e "\nFailed Tests:"
	for file in $failed_test; do
		echo "- $file"
	done
	echo -e "\n$fails Tests failed!"
else
	echo "All tests passed!"
fi

rm temp.txt &> /dev/null
