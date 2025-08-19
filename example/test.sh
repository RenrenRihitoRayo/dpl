mkdir "errors" &> /dev/null

failed_test=()
timed_out=()
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
		timeout 5s python3 ../dpl.py -simple-mode -simple-run $file &> temp.txt
		command_res=$?
		if [ "$command_res" -eq "124" ]; then
			echo "$file: took more than 5 seconds!"
			timed_out+=($file)
			continue
		fi
		if [ "$command_res" -ne "0" ]; then
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
	echo -e "\nTests that timed out:"
	for file in "${timed_out[@]}"; do
		echo "- $file"
	done
fi

if [ $fails -ne 0 ]; then
	echo -e "\nFailed Tests:"
	for file in "${failed_test[@]}"; do
		echo "- $file"
	done
	echo -e "\n$fails Tests failed!"
else
	echo "All tests passed!"
fi

rm temp.txt &> /dev/null