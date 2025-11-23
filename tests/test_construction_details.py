from flectra import fields
from flectra.tests import common


class TestConstructionDetails(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.construction_model = self.env["construction.details"]
        self.site = self.env["construction.site"].create({
            "name": "Test Site",
        })
        self.customer = self.env["res.partner"].create({
            "name": "Test Customer",
            "is_construction_company": True,
        })

    def _create_construction(self, extra_vals=None):
        values = {
            "site_id": self.site.id,
        }
        if extra_vals:
            values.update(extra_vals)
        return self.construction_model.create(values)

    def test_sequence_assigned_on_create(self):
        record = self._create_construction()

        self.assertTrue(
            record.name,
            "Sequence should assign a non-empty identifier to construction jobs.",
        )
        self.assertNotEqual(
            record.name,
            "New",
            "Sequence must replace the default placeholder value.",
        )
        self.assertEqual(
            record.stage,
            "confirm",
            "New construction records should start in the confirm stage.",
        )
        self.assertEqual(
            record.company_id,
            self.env.company,
            "Company should default to the current company.",
        )
        self.assertEqual(
            record.currency_id,
            self.env.company.currency_id,
            "Currency must follow the company’s currency through the related field.",
        )

    def test_name_get_uses_site_and_sequence(self):
        record = self._create_construction()
        label = dict(record.name_get())[record.id]
        expected = f"{record.site_id.name} - {record.name}"
        self.assertEqual(label, expected)

    def test_inspection_wizard_creates_project_task(self):
        construction = self._create_construction({
            "customer_company_id": self.customer.id,
        })
        construction.action_start_construction()

        wizard = self.env["construction.inspection"].create({
            "name": "Safety Inspection",
            "construction_id": construction.id,
            "user_ids": [(6, 0, [self.env.user.id])],
            "deadline": fields.Date.today(),
        })
        wizard.action_create_task()

        task = self.env["project.task"].search([
            ("construction_id", "=", construction.id),
            ("is_inspection_task", "=", True),
        ], limit=1)
        self.assertTrue(task, "Inspection wizard should create a task record.")
        self.assertEqual(task.user_id, self.env.user, "Primary assignee should default to the selected user.")
        self.assertIn(self.env.user, task.allowed_user_ids, "Inspection task should grant visibility to selected users.")
        self.assertIn(self.env.user.partner_id, task.message_partner_ids,
                      "Selected users must be subscribed to the inspection task.")

        inspection = self.env["site.inspection"].search([
            ("construction_id", "=", construction.id),
            ("task_id", "=", task.id),
        ], limit=1)
        self.assertTrue(inspection, "Inspection record must link back to the generated task.")
