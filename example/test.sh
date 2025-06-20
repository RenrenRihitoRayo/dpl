mkdir "errors" &> /dev/null

fails=0

for file in *; do
	if [ -f "$file" ]; then
		if [ "${file##*.}" != "dpl" ]; then
			continue	
		fi
		python3 ../dpl.py -simple-run -no-lupa -no-cffi $file &> temp.txt 
		if [ "$?" -ne "0" ]; then
			echo "$file: Failed [$?]"
			cp temp.txt "./errors/${file}.err"
			fails=$((fails + 1))
			continue
		fi
		echo "$file: Passed"
	fi
done

if [ $fails -ne 0 ]; then
	echo "$fails Tests failed!"
else
	echo "All tests passed!"
fi
