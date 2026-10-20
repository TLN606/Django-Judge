document.addEventListener('DOMContentLoaded', function () {

    const container =
        document.getElementById(
            'test-cases-container'
        );

    const addButton =
        document.getElementById(
            'add-test-case-btn'
        );

    const totalForms =
        document.getElementById(
            'id_test_cases-TOTAL_FORMS'
        );

    const countDisplay =
        document.getElementById(
            'test-case-count'
        );

    const template =
        document.getElementById(
            'empty-test-case-template'
        );


    /*
    =========================================================
    CHECK ELEMENTS
    =========================================================
    */

    if (!container) {

        console.error(
            'test-cases-container not found.'
        );

        return;

    }


    if (!addButton) {

        console.error(
            'add-test-case-btn not found.'
        );

        return;

    }


    if (!totalForms) {

        console.error(
            'TOTAL_FORMS not found.'
        );

        return;

    }


    if (!countDisplay) {

        console.error(
            'test-case-count not found.'
        );

        return;

    }


    if (!template) {

        console.error(
            'empty-test-case-template not found.'
        );

        return;

    }


    /*
    =========================================================
    GET VISIBLE CARDS
    =========================================================
    */

    function getVisibleCards() {

        return Array.from(
            container.querySelectorAll(
                '.test-case-card'
            )
        ).filter(function (card) {

            return card.style.display !== 'none';

        });

    }


    /*
    =========================================================
    UPDATE NUMBERS
    =========================================================
    */

    function updateNumbers() {

        const cards =
            getVisibleCards();


        cards.forEach(function (
            card,
            index
        ) {

            const number =
                card.querySelector(
                    '.test-case-number'
                );


            const title =
                card.querySelector(
                    '.test-case-title-text'
                );


            const displayNumber =
                index + 1;


            if (number) {

                number.textContent =
                    displayNumber;

            }


            if (title) {

                title.textContent =
                    'Test Case ' +
                    displayNumber;

            }

        });


        const count =
            cards.length;


        countDisplay.textContent =
            count +
            (
                count === 1
                    ? ' Test Case'
                    : ' Test Cases'
            );

    }


    /*
    =========================================================
    UPDATE REMOVE BUTTONS
    =========================================================
    */

    function updateRemoveButtons() {

        const cards =
            getVisibleCards();


        cards.forEach(function (card) {

            const button =
                card.querySelector(
                    '.test-case-remove-btn'
                );


            if (!button) {
                return;
            }


            if (cards.length <= 1) {

                button.style.display =
                    'none';

            } else {

                button.style.display =
                    'flex';

            }

        });

    }


    /*
    =========================================================
    ADD TEST CASE
    =========================================================
    */

    addButton.addEventListener(
        'click',
        function () {

            /*
            Current number of Django forms.

            Example:

            1
            -> new index = 1

            2
            -> new index = 2

            3
            -> new index = 3
            */

            const formIndex =
                parseInt(
                    totalForms.value,
                    10
                );


            /*
            Get template HTML
            */

            let html =
                template.innerHTML;


            /*
            Replace Django __prefix__
            with actual form index
            */

            html =
                html.replace(
                    /__prefix__/g,
                    formIndex
                );


            /*
            Replace display number
            */

            html =
                html.replace(
                    /__NUMBER__/g,
                    formIndex + 1
                );


            /*
            Convert HTML string to DOM
            */

            const wrapper =
                document.createElement(
                    'div'
                );


            wrapper.innerHTML =
                html.trim();


            const newCard =
                wrapper.firstElementChild;


            if (!newCard) {

                console.error(
                    'Cannot create new Test Case.'
                );

                return;

            }


            /*
            Add new card
            */

            container.appendChild(
                newCard
            );


            /*
            IMPORTANT

            Tell Django that the formset
            now contains one more form.
            */

            totalForms.value =
                formIndex + 1;


            /*
            Update UI
            */

            updateNumbers();

            updateRemoveButtons();

        }
    );


    /*
    =========================================================
    REMOVE TEST CASE
    =========================================================
    */

    window.removeTestCase =
        function (button) {

            const card =
                button.closest(
                    '.test-case-card'
                );


            if (!card) {
                return;
            }


            /*
            Find DELETE checkbox
            */

            const deleteInput =
                card.querySelector(
                    'input[name$="-DELETE"]'
                );


            /*
            Tell Django to delete
            this form during submit.
            */

            if (deleteInput) {

                deleteInput.checked =
                    true;

            }


            /*
            Hide card
            */

            card.style.display =
                'none';


            /*
            Update UI
            */

            updateNumbers();

            updateRemoveButtons();

        };


    /*
    =========================================================
    INITIAL STATE
    =========================================================
    */

    updateNumbers();

    updateRemoveButtons();

});