mkdir "errors" &> /dev/null

failed_test=()
timed_out=()
fails=0
time=5s

for file in *; do
	if [ "${file%%-*}" = "xx" ]; then
		continue
	fi
	if [ -f "$file" ]; then
		if [ "${file##*.}" != "dpl" ]; then
			continue
		fi
		echo -n "$file: "
		timeout $time python3 ../dpl.py -simple-mode -simple-run $file &> temp.txt
		command_res=$?
		if [ "$command_res" -eq "124" ]; then
			if file_msg=$(grep "^$file :timeout: " "excluded.txt"); then
		        echo -e ${file_msg#* :timeout: }
		        continue
		    elif file_msg=$(grep "^$file :: " "excluded.txt"); then
		        echo -e ${file_msg#* :: }
		        continue
		    else
    		    echo -e "\033[0;33mTimeout ($time)\033[0m"
                timed_out+=($file)
    			continue
			fi
			continue
		fi
		if [ "$command_res" -ne "0" ]; then
		    if file_msg=$(grep "^$file :$command_res: " "excluded.txt"); then
		        echo -e ${file_msg#* :$command_res: }
		    elif file_msg=$(grep "^$file :: " "excluded.txt"); then
		        echo -e ${file_msg#* :: }
		    else
    		    echo -e "\031[0;32mFailed [$command_res]\033[0m"
    			cp temp.txt "./errors/${file}.err"
    			fails=$((fails + 1))
    			failed_test+=($file)
			fi
			continue
		fi
		echo -e "\033[0;32mPassed\033[0m"
	fi
done

if [[ ! ${#timed_out[@]} ]]; then
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
elif [ $fails -eq 0 ] && [ ${#timed_out[@]} == 0 ]; then
	echo -e "\033[0;32mAll tests passed!\033[0m"
else
    echo -e "\031[0;32mSome tests failed!\033[0m"
fi

rm temp.txt &> /dev/null
