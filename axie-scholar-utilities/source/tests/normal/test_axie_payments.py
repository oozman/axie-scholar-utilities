import os
import sys
import builtins
import logging

from mock import patch, call, mock_open
from glob import glob
import pytest

from axie import AxiePaymentsManager
from axie.payments import Payment, PaymentsSummary
from axie.utils import SLP_CONTRACT
from tests.test_utils import LOG_FILE_PATH, cleanup_log_file


@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""
    def remove_log_files():
        files = glob(LOG_FILE_PATH+'logs/*.log')
        for f in files:
            os.remove(f)
    request.addfinalizer(remove_log_files)


def test_payments_manager_init():
    payments_file = "sample_payments_file.json"
    secrets_file = "sample_secrets_file.json"
    axp = AxiePaymentsManager(payments_file, secrets_file)
    assert axp.auto is False
    axp2 = AxiePaymentsManager(payments_file, secrets_file, auto=True)
    assert axp2.auto is True


def test_payments_manager_verify_input_success():
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "scholars": [{
            "name": "Scholar 1",
            "ronin": scholar_acc,
            "splits": [
                {
                    "persona": "Manager",
                    "percentage": 44,
                    "ronin": manager_acc
                },
                {
                    "persona": "Scholar",
                    "percentage": 40,
                    "ronin": "ronin:<scholar_1_address>"
                },
                {
                    "persona": "Other Person",
                    "percentage": 6,
                    "ronin": "ronin:<other_person_address>"
                },
                {
                    "persona": "Trainer",
                    "percentage": 10,
                    "ronin": "ronin:<trainer_address>"
                }
        ]}],
        "donations": [{
            "name": "Entity 1",
            "ronin": dono_acc,
            "percentage": 1
        }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    assert axp.manager_acc == None
    assert axp.type == "new"
    assert axp.scholar_accounts == p_file['scholars']
    assert axp.donations == p_file['donations']


def test_payments_manager_verify_input_success_percent():
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 1
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    assert axp.manager_acc == manager_acc
    assert axp.type == "legacy"
    assert axp.scholar_accounts == p_file['Scholars']
    assert axp.donations == p_file['Donations']


def test_payments_manager_verify_input_success_percent_with_payouts():
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "ScholarPayout":10,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 1
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    assert axp.manager_acc == manager_acc
    assert axp.type == "legacy"
    assert axp.scholar_accounts == p_file['Scholars']
    assert axp.donations == p_file['Donations']


def test_payments_manager_verify_input_manager_ronin_short(caplog):
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    dono_acc = 'ronin:<donations_address>'
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "ScholarPayout":10,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 1
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    with patch.object(sys, "exit") as mocked_sys:
        axp = AxiePaymentsManager(p_file, s_file)
        axp.verify_inputs()
    mocked_sys.assert_called_once()
    assert "Please review the ronins in your donations. One or more are wrong!" in caplog.text


def test_payments_manager_verify_input_donations_exceed_max(caplog):
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "ScholarPayout":10,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 1
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 100
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    with patch.object(sys, "exit") as mocked_sys:
        axp = AxiePaymentsManager(p_file, s_file)
        axp.verify_inputs()
    mocked_sys.assert_called()
    print(caplog.text)
    assert "Error given: 100 is greater than the maximum of 98\nFor attribute in: ['Donations', 0, 'Percent']" in caplog.text


def test_payments_manager_verify_input_missing_private_key(caplog):
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "ScholarPayout":10,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 1
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {}
    with patch.object(sys, "exit") as mocked_sys:
        axp = AxiePaymentsManager(p_file, s_file)
        axp.verify_inputs()
    mocked_sys.assert_called_once()
    assert "Account 'Scholar 1' is not present in secret file, please add it." in caplog.text


def test_payments_manager_verify_input_invalid_private_key(caplog):
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345'
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "ScholarPayout":10,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 1
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    with patch.object(sys, "exit") as mocked_sys:
        axp = AxiePaymentsManager(p_file, s_file)
        axp.verify_inputs()
    mocked_sys.assert_called()
    assert f"Private key for account {scholar_acc} is not valid, please review it!" in caplog.text
    assert ("There is a problem with your secrets.json, delete it and re-generate the file starting with "
            "an empty secrets file.Or open it and see what is wrong with the keys of the accounts reported above." in caplog.text)


@patch("axie.AxiePaymentsManager.prepare_new_payout")
@patch("axie.AxiePaymentsManager.prepare_old_payout")
def test_payments_manager_prepare_payout_check_correct_calcs_legacy(mocked_prepare_old_payout, mocked_prepare_new_payout):
    axp = AxiePaymentsManager({}, {})
    axp.type = 'legacy'
    axp.prepare_payout()
    mocked_prepare_new_payout.assert_not_called()
    mocked_prepare_old_payout.assert_called_once()


@patch("axie.AxiePaymentsManager.prepare_new_payout")
@patch("axie.AxiePaymentsManager.prepare_old_payout")
def test_payments_manager_prepare_payout_check_correct_calcs_new(mocked_prepare_old_payout, mocked_prepare_new_payout):
    axp = AxiePaymentsManager({}, {})
    axp.type = 'new'
    axp.prepare_payout()
    mocked_prepare_old_payout.assert_not_called()
    mocked_prepare_new_payout.assert_called_once()


@patch("axie.payments.check_balance", return_value=1000)
@patch("axie.AxiePaymentsManager.payout_account")
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=True)
def test_payments_manager_prepare_payout_check_correct_payments_legacy(mocked_enough_balance,
                                                                       mocked_payout,
                                                                       mocked_check_balance):
    scholar_acc = 'ronin:12345678900987654321' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:12345678900987000321' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    clean_scholar_acc = scholar_acc.replace("ronin:", "0x")
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 45,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 10
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    axp.prepare_payout()
    mocked_check_balance.assert_called()
    mocked_enough_balance.assert_called_with(scholar_acc, 1000)
    mocked_payout.assert_called_once()
    # 1st payment
    assert mocked_payout.call_args[0][0] == "Scholar 1"
    assert mocked_payout.call_args[0][1][0].name == "Payment to scholar of Scholar 1"
    assert mocked_payout.call_args[0][1][0].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][0].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][0].amount == 450
    # 2nd payment
    assert mocked_payout.call_args[0][1][1].name == "Payment to trainer of Scholar 1"
    assert mocked_payout.call_args[0][1][1].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][1].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][1].amount == 100
    # 3rd payment (dono)
    assert mocked_payout.call_args[0][1][2].name == "Donation to Entity 1 for Scholar 1"
    assert mocked_payout.call_args[0][1][2].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][2].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][2].amount == round(1000*0.01)
    # 4th Payment (fee)
    assert mocked_payout.call_args[0][1][3].name == "Donation to software creator for Scholar 1"
    assert mocked_payout.call_args[0][1][3].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][3].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][3].amount == round(1000*0.01)
    # 5th Payment
    assert mocked_payout.call_args[0][1][4].name == "Payment to manager of Scholar 1"
    assert mocked_payout.call_args[0][1][4].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][4].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][4].amount == 1000 - 550 - round(1000*0.02)
    assert len(mocked_payout.call_args[0][1]) == 5


@patch("axie.payments.check_balance", return_value=1000)
@patch("axie.AxiePaymentsManager.payout_account")
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=True)
def test_payments_manager_prepare_payout_check_correct_payments_new(mocked_enough_balance,
                                                                    mocked_payout,
                                                                    mocked_check_balance):
    scholar_acc = 'ronin:12345678900987654321' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:12345678900987000321' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    clean_scholar_acc = scholar_acc.replace("ronin:", "0x")
    p_file = {
        "scholars": [{
            "name": "Scholar 1",
            "ronin": scholar_acc,
            "splits": [
                {
                    "persona": "Manager",
                    "percentage": 43,
                    "ronin": manager_acc
                },
                {
                    "persona": "Scholar",
                    "percentage": 40,
                    "ronin": "ronin:<scholar_1_address>"
                },
                {
                    "persona": "Other Person",
                    "percentage": 6,
                    "ronin": "ronin:<other_person_address>"
                },
                {
                    "persona": "Trainer",
                    "percentage": 10,
                    "ronin": "ronin:<trainer_address>"
                }
        ]}],
        "donations": [{
            "name": "Entity 1",
            "ronin": dono_acc,
            "percentage": 1
        }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    axp.prepare_payout()
    mocked_check_balance.assert_called()
    mocked_enough_balance.assert_called_with(scholar_acc, 970)
    mocked_payout.assert_called_once()
    # 1st payment
    assert mocked_payout.call_args[0][0] == "Scholar 1"
    assert mocked_payout.call_args[0][1][0].name == "Payment to Manager of Scholar 1"
    assert mocked_payout.call_args[0][1][0].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][0].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][0].amount == 410
    # 2nd payment
    assert mocked_payout.call_args[0][1][1].name == "Payment to Scholar of Scholar 1"
    assert mocked_payout.call_args[0][1][1].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][1].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][1].amount == 400
    # 3rd payment
    assert mocked_payout.call_args[0][1][2].name == "Payment to Other Person of Scholar 1"
    assert mocked_payout.call_args[0][1][2].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][2].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][2].amount == 60
    # 4th payment
    assert mocked_payout.call_args[0][1][3].name == "Payment to Trainer of Scholar 1"
    assert mocked_payout.call_args[0][1][3].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][3].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][3].amount == 100
    # 5th payment (dono)
    assert mocked_payout.call_args[0][1][4].name == "Donation to Entity 1 for Scholar 1"
    assert mocked_payout.call_args[0][1][4].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][4].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][4].amount == 10
    # 6th Payment (fee)
    assert mocked_payout.call_args[0][1][5].name == "Donation to software creator for Scholar 1"
    assert mocked_payout.call_args[0][1][5].from_acc == clean_scholar_acc
    assert mocked_payout.call_args[0][1][5].from_private == scholar_private_acc
    assert mocked_payout.call_args[0][1][5].amount == 10
    assert len(mocked_payout.call_args[0][1]) == 6


@patch("axie.payments.check_balance", return_value=0)
@patch("axie.AxiePaymentsManager.payout_account")
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=True)
def test_payments_manager_prepare_payout_check_correct_payments_percent_no_balance(mocked_enough_balance,
                                                                                   mocked_payout,
                                                                                   mocked_check_balance):
    scholar_acc = 'ronin:12345678900987654321' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:12345678900987000321' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 45,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 10
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    axp.prepare_payout()
    mocked_check_balance.assert_called()
    mocked_enough_balance.assert_called_with(scholar_acc, 0)
    mocked_payout.assert_not_called()


@patch("axie.payments.check_balance", return_value=100)
@patch("axie.AxiePaymentsManager.payout_account")
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=False)
def test_payments_manager_prepare_no_payout_not_enough_balance(mocked_check_balance,
                                                               mocked_payout,
                                                               _):
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 90,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 10
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    axp.prepare_payout()
    mocked_check_balance.assert_called_with(scholar_acc, 101)
    mocked_payout.assert_not_called()


@patch("axie.payments.check_balance", return_value=1000)
@patch("axie.payments.Payment.execute", return_value=("abc123", True))
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=True)
@patch("axie.payments.get_nonce", return_value=1)
def test_payments_manager_payout_account_accept(_, mocked_check_balance, mocked_execute, __, caplog):
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 10
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    with caplog.at_level(logging.DEBUG):
        with patch.object(builtins, 'input', lambda _: 'y'):
            axp.prepare_payout()
        mocked_check_balance.assert_called_with(scholar_acc, 1000)
        assert mocked_execute.call_count == 5
        assert "Payment to scholar of Scholar 1(ronin:<scholar_address>) for the amount of 500 SLP" in caplog.text
        assert "Payment to trainer of Scholar 1(ronin:<trainer_address>) for the amount of 100 SLP" in caplog.text
        assert (f"Donation to Entity 1 for Scholar 1({dono_acc}) for the amount of 10 SLP" in caplog.text)
        assert ("Donation to software creator for Scholar 1(ronin:9fa1bc784c665e683597d3f29375e45786617550) "
                "for the amount of 10 SLP" in caplog.text)
        assert f"Payment to manager of Scholar 1({manager_acc}) for the amount of 380 SLP" in caplog.text
        assert "Transactions completed for account: 'Scholar 1'" in caplog.text


@patch("axie.payments.check_balance", return_value=1000)
@patch("axie.payments.Payment.execute", return_value=("abc123", True))
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=True)
@patch("axie.payments.get_nonce", return_value=1)
def test_payments_manager_payout_auto_yes(_, mocked_check_balance, mocked_execute, __, caplog):
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 10
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file, auto=True)
    axp.verify_inputs()
    with caplog.at_level(logging.INFO):
        axp.prepare_payout()
        mocked_check_balance.assert_called_with(scholar_acc, 1000)
        assert mocked_execute.call_count == 5
        assert "Payment to scholar of Scholar 1(ronin:<scholar_address>) for the amount of 500 SLP" in caplog.text
        assert "Payment to trainer of Scholar 1(ronin:<trainer_address>) for the amount of 100 SLP" in caplog.text
        assert (f"Donation to Entity 1 for Scholar 1({dono_acc}) for the amount "
                "of 10 SLP" in caplog.text)
        assert ("Donation to software creator for Scholar 1(ronin:9fa1bc784c665e683597d3f29375e45786617550) "
                "for the amount of 10 SLP" in caplog.text)
        assert f"Payment to manager of Scholar 1({manager_acc}) for the amount of 380 SLP" in caplog.text
        assert "Transactions completed for account: 'Scholar 1'" in caplog.text
        assert "Transactions Summary:" in caplog.text


@patch("axie.payments.check_balance", return_value=1000)
@patch("axie.payments.Payment.execute")
@patch("axie.AxiePaymentsManager.check_acc_has_enough_balance", return_value=True)
@patch("axie.payments.get_nonce", return_value=1)
def test_payments_manager_payout_account_deny(_, mocked_check_balance, mocked_execute, __, caplog):
    scholar_acc = 'ronin:<account_s1_address>' + "".join([str(x) for x in range(10)]*2)
    manager_acc = 'ronin:<manager_address>000' + "".join([str(x) for x in range(10)]*2)
    dono_acc = 'ronin:<donations_address>0' + "".join([str(x) for x in range(10)]*2)
    scholar_private_acc = '0x<account_s1_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    p_file = {
        "Manager": manager_acc,
        "Scholars": [
            {
                "Name":"Scholar 1", 
                "AccountAddress": scholar_acc,
                "ScholarPayoutAddress": "ronin:<scholar_address>",
                "ScholarPercent": 50,
                "TrainerPayoutAddress": "ronin:<trainer_address>",
                "TrainerPercent": 10
            }],
        "Donations": [
            {
                "Name": "Entity 1",
                "AccountAddress": dono_acc,
                "Percent": 1
            }]
    }
    s_file = {scholar_acc: scholar_private_acc}
    axp = AxiePaymentsManager(p_file, s_file)
    axp.verify_inputs()
    with patch.object(builtins, 'input', lambda _: 'n'):
        axp.prepare_payout()
    mocked_check_balance.assert_called_with(scholar_acc, 1000)
    mocked_execute.assert_not_called()
    assert "Transactions canceled for account: 'Scholar 1'" in caplog.text


@patch("web3.eth.Eth.contract", return_value="contract")
@patch("web3.Web3.toChecksumAddress")
def test_payment_get_nonce_calls_w3_low_nonce(mocked_checksum, mock_contract):
    s = PaymentsSummary()
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')) as mock_file:
        p = Payment(
            "random_account",
            "manager",
            "ronin:from_ronin",
            "ronin:from_private_ronin",
            "ronin:to_ronin",
            10,
            s)
    mock_file.assert_called_with("axie/slp_abi.json", encoding='utf-8')
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mock_contract.assert_called()
    assert p.contract == "contract"
    assert p.name == "random_account"
    assert p.payment_type == "manager"
    assert p.from_acc == "0xfrom_ronin"
    assert p.from_private == "ronin:from_private_ronin"
    assert p.to_acc == "0xto_ronin"
    assert p.amount == 10
    assert p.summary == s


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_calls_web3_functions(mock_transaction_receipt,
                                      mock_contract,
                                      mock_keccak,
                                      mock_to_hex,
                                      mock_send,
                                      mock_sign,
                                      mock_checksum,
                                      _,
                                      caplog):
    # Make sure file is clean to start
    log_file = glob(LOG_FILE_PATH+'logs/results_*.log')[0][9:]
    cleanup_log_file(log_file)
    PaymentsSummary().clear()
    s = PaymentsSummary()
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')) as mock_file:
        p = Payment(
            "random_account",
            "manager",
            "ronin:from_ronin",
            "ronin:from_private_ronin",
            "ronin:to_ronin",
            10,
            s)
        p.execute()
    mock_file.assert_called_with("axie/slp_abi.json", encoding='utf-8')
    mock_contract.assert_called_with(address="checksum", abi={"foo": "bar"})
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    assert mock_sign.call_args[1]['private_key'] == "ronin:from_private_ronin"
    mock_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call('0xfrom_ronin'),
        call('0xto_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")
    assert ('Transaction random_account(ronin:to_ronin) for the amount of 10 SLP completed! Hash: transaction_hash - '
            'Explorer: https://explorer.roninchain.com/tx/transaction_hash' in caplog.text)
    assert str(s) == "Paid 1 managers, 10 SLP.\n"
    with open(log_file) as f:
        lf = f.readlines()
        assert len(lf) == 1
    assert ("Important: Transaction random_account(ronin:to_ronin) for the amount of 10 SLP completed! "
            "Hash: transaction_hash - Explorer: https://explorer.roninchain.com/tx/transaction_hash") in lf[0]
    cleanup_log_file(log_file)


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("axie.payments.Payment.send_replacement_tx")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 0})
def test_execute_calls_web3_functions_retry(mock_transaction_receipt,
                                            mock_contract,
                                            mock_keccak,
                                            mock_to_hex,
                                            mock_send,
                                            mock_sign,
                                            mock_checksum,
                                            mock_replacement_tx,
                                            _,
                                            caplog):
    # Make sure file is clean to start
    log_file = glob(LOG_FILE_PATH+'logs/results_*.log')[0][9:]
    cleanup_log_file(log_file)
    PaymentsSummary().clear()
    s = PaymentsSummary()
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')) as mock_file:
        p = Payment(
            "random_account",
            "manager",
            "ronin:from_ronin",
            "ronin:from_private_ronin",
            "ronin:to_ronin",
            10,
            s)
        p.execute()
    mock_file.assert_called_with("axie/slp_abi.json", encoding='utf-8')
    mock_contract.assert_called_with(address="checksum", abi={"foo": "bar"})
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    assert mock_sign.call_args[1]['private_key'] == "ronin:from_private_ronin"
    mock_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call('0xfrom_ronin'),
        call('0xto_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")
    mock_replacement_tx.assert_called_with(123)
    assert ("Important: Transaction random_account(ronin:to_ronin) for the amount of 10 SLP failed. "
            "Trying to replace it with a 0 value tx and re-try." in caplog.text)
    with open(log_file) as f:
        lf = f.readlines()
        assert len(lf) == 1
    assert ("Important: Transaction random_account(ronin:to_ronin) for the amount of 10 SLP failed. "
            "Trying to replace it with a 0 value tx and re-try.") in lf[0]
    assert str(s) == "No payments made!"
    cleanup_log_file(log_file)
