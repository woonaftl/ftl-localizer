"""How to use:
    localize function: Prepares xml files for localization by moving
    all text strings from data files into separate text files which
    can be different for each language.

    :param workdir: Work directory where all input xml files are located.

    :param outputdir: Creates a folder with this name
        and puts all result files there.

    :param language_attr: Determines xml attribute "language"
        in result localization file.
        ('de', 'es', 'fr', 'it', 'pl', 'pt', 'ru', 'zh-Hans')

    :param check_same_strings: If True, tries to combine
        exactly same text strings into one.

    :param split_result: If False, all files with text strings will be
        combined, otherwise, files will be split into categories based
        on source file.


    delocalize function: Makes xml files more convenient to edit by
    inserting text strings from separate text files directly into
    data files.

    :param workdir: Work directory where all input xml files are located.

    :param outputdir: Creates a folder with this name
        and puts all result files there.

    :param language_attr: Determines xml attribute "language" which will
        be searched in text files for insertion into data files.
        ('de', 'es', 'fr', 'it', 'pl', 'pt', 'ru', 'zh-Hans')

    :param empty_string: If there is no text string with selected language
        found, this will be inserted instead, to help find missing strings.

    :param ignore_continue: If True, do not replace continue id
        with Continue... text.

Инструкция:
    localize: Подготовить файлы для локализации, скопировав все строки
    из файлов с данными (события, орудия) в отдельные файлы текстов,
    которые могут отличаться для разных языков.

    :param workdir: Рабочая директория (там где расположены исходные файлы).

    :param outputdir: Выходная директория (куда скопировать результат).

    :param language_attr: Атрибут "language", который будет использоваться
        в выходных файлах.
        ('de', 'es', 'fr', 'it', 'pl', 'pt', 'ru', 'zh-Hans')

    :param check_same_strings: Если True, то попытаться найти одинаковые
        строки и присвоить им один и тот же id для того, чтобы не было
        повторений в выходных файлах.

    :param split_result: Если False, то все файлы с текстами будут объединены
        в один, иначе, файлы будут разбиты по категориям.
        (events, blueprints, misc...)


    delocalize: Для удобства редактирования, переместить все строки из
    отдельных файлов с текстами в файлы с данными (события, орудия).

    :param workdir: Рабочая директория (там где расположены исходные файлы).

    :param outputdir: Выходная директория (куда скопировать результат).

    :param language_attr: Значение атрибута "language" для поиска в текстовых
        файлах. ('de', 'es', 'fr', 'it', 'pl', 'pt', 'ru', 'zh-Hans').

    :param empty_string: Если по заданному id не найдено текста на заданном
        языке, id будет заменен на эту строку (чтобы потом было проще найти
        непереведенные строки).

    :param ignore_continue: Если True, не заменять "continue" текстом
        Продолжить...

    Don't forget to put double \\ for Windows paths
    Не забудьте поставить двойные \\ в путях на Windows
"""

from ftl_localizer import localize, delocalize

localize('C:\\Test123\\my_mod\\data',
         'C:\\Test123\\my_mod\\result0',
         'ru',
         True,
         False)

delocalize('C:\\Test123\\my_mod\\result0',
           'C:\\Test123\\my_mod\\result1',
           'ru',
           'TEXT_NOT_FOUND',
           True)
