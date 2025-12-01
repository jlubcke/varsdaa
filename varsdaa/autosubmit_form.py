from django.template import Template
from iommi import Asset

from varsdaa.iommi import Form


# language=javascript
AUTO_SUBMIT_JS = \
    """
    window.addEventListener('iommi.init.start', function (event) {
        console.log(event);
        document.querySelectorAll('.iommi_auto_submit').forEach(
            form => autoSubmitForm(form)
        );
    });

    function autoSubmitForm(form) {
        form.setAttribute('autocomplete', 'off');

        const debouncedPopulate = window.iommi.debounce(window.iommi.queryPopulate, 400);

        let prevData = new FormData(form);
        const onChange = e => {
            const formData = new FormData(form);
            if (window.iommi.hasSameData(prevData, formData)) {
                return;
            }
            prevData = formData;

            const fieldType = e.target.getAttribute('type');
            if (fieldType === 'file' && form.method === 'get') {
                // don't do anything
                // iommi endpoints are for GET only and files cannot be sent via GET
                // if you really need a file-input in the filter form, you have to add your own listener on change
            } else if (fieldType === 'text') {
                if (e.type === 'change') {
                    // change event fire when the input loses focus. We have already
                    // populated the form on the input event so ignore it
                    return;
                }
                // delay ajax request for free text
                window.iommi.debouncedPopulate(form, e.target);
            } else {
                // select2 elements have hidden inputs when they update GUI should respond immediately
                // same goes for checkboxes
                submitForm(form);
            }
        };
        ['change', 'input', 'switch-mode'].forEach(eventType => {
            form.addEventListener(eventType, onChange);
        });

        Array.from(form.getElementsByClassName('select2')).forEach(s => {
            s.addEventListener('change', onChange);
        });

        const submitButton = form.querySelector('[data-iommi-submit-button]');
        const actionsContainer = submitButton.parentNode;
        submitButton.remove();
        if (actionsContainer.children.length === 0) {
            actionsContainer.remove();
        }
    }

    function submitForm(form) {
        const formData = new FormData(form);

        // we need to preserve url for other forms
        let params;
        try {
            params = new URL(window.location.href).searchParams;
        } catch {
            params = new URLSearchParams(window.location.href);
        }

        // first remove from URL params all that belongs to this form
        const deleteParams = new Set();
        for (const [key, value] of params) {
            if (typeof form.elements[key] !== "undefined") {
                deleteParams.add(key);
            }
        }
        for (let key of deleteParams) {
            params.delete(key);
        }

        // append to URL params only applied filters
        for (const [key, value] of formData) {
            if (value && !(value instanceof File)) {
                // new URLSearchParams(formData) would throw an error for files
                params.append(key, value);
            }
        }
        window.location = `${window.location.pathname}?${params.toString()}`;
    }
    """

class AutosubmitForm(Form):
    class Meta:
        attrs__method="GET"
        attrs__class__iommi_auto_submit=True
        actions__submit=dict(
            include=True,
            attrs={"data-iommi-submit-button": ""},
        )
        assets__auto_submit=Asset.js(Template(AUTO_SUBMIT_JS))
