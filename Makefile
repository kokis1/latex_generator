setup:
	conda env create -f environment.yml

update:
	conda env update -f environment.yml --prune

clean:
	conda env remove -n latex_generator

